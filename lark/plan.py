"""Wing, Hearth, and Wander price a trip against one budget."""

from __future__ import annotations

import math
from datetime import date, timedelta

from lark import live
from lark.catalog import CITIES, destination, origin
from lark.parse import total_budget

CARRIERS = {
    "europe": [("TAP Air Portugal", "TP"), ("Iberia", "IB"), ("Delta", "DL"), ("United", "UA"), ("Air France", "AF")],
    "japan": [("ANA", "NH"), ("Japan Airlines", "JL"), ("United", "UA")],
    "mexico": [("Aeroméxico", "AM"), ("United", "UA"), ("Volaris", "Y4")],
    "iceland": [("Icelandair", "FI"), ("Delta", "DL")],
    "morocco": [("Royal Air Maroc", "AT"), ("Iberia", "IB")],
    "domestic": [("Delta", "DL"), ("JetBlue", "B6"), ("United", "UA")],
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def approx_tz(lon: float) -> int:
    return int(round((lon + 7.5) / 15))


def money_round(amount: float) -> int:
    return int(round(amount / 10.0) * 10)


def fare_per_person(km: float, month: int, stops: int) -> int:
    if km < 800:
        base = 120 + km * 0.18
    elif km < 2200:
        base = 160 + km * 0.10
    elif km < 6000:
        base = 280 + km * 0.065
    else:
        base = 420 + km * 0.05
    if month in (6, 7, 8, 12):
        base *= 1.14
    elif month in (1, 2, 11):
        base *= 0.84
    if stops == 0:
        base *= 1.12
    else:
        base *= 0.86
    return max(90, money_round(base))


def clock(hour: float) -> str:
    hour = hour % 24
    whole = int(hour)
    minute = int(round((hour - whole) * 60))
    if minute == 60:
        whole += 1
        minute = 0
        whole %= 24
    suffix = "AM" if whole < 12 else "PM"
    shown = whole % 12 or 12
    return f"{shown}:{minute:02d} {suffix}"


def duration_label(hours: float) -> str:
    whole = int(hours)
    minute = int(round((hours - whole) * 60))
    if minute == 60:
        whole += 1
        minute = 0
    return f"{whole}h {minute:02d}m"


def pretty_date(iso: str) -> str:
    day = date.fromisoformat(iso)
    return f"{day.strftime('%a')} {day.strftime('%b')} {day.day}"


def season_line(city: dict, month: int) -> str:
    if month in city["best_months"]:
        return city["good_season"]
    if month in city["tough_months"]:
        return city["tough_season"]
    return city["shoulder_season"]


def meal_rate(state: dict) -> int:
    vibes = set(state.get("vibes") or [])
    if state.get("preference") == "cheaper":
        return 30
    if "food" in vibes or state.get("preference") == "more_play":
        return 58
    if "quiet" in vibes:
        return 36
    return 42


def activity_cost(activity: dict, travelers: int) -> int:
    if activity["per"] == "person":
        return int(activity["price"]) * travelers
    return int(activity["price"])


def select_activities(catalog: list[dict], vibes: set[str], money: int, preference: str, travelers: int) -> list[dict]:
    def rank(activity: dict) -> tuple:
        overlap = len(set(activity["tags"]) & vibes)
        cost = activity_cost(activity, travelers)
        return (overlap, 1 if cost == 0 else 0, -cost)

    chosen = []
    spent = 0
    cap = 4 if preference == "cheaper" else 5
    for activity in sorted(catalog, key=rank, reverse=True):
        cost = activity_cost(activity, travelers)
        if preference == "cheaper" and cost > 50 and len(chosen) >= 2:
            continue
        if cost == 0 or spent + cost <= money:
            chosen.append(
                {
                    "name": activity["name"],
                    "area": activity["area"],
                    "cost": cost,
                    "note": activity["note"],
                    "tags": list(activity["tags"]),
                }
            )
            spent += cost
        if len(chosen) >= cap:
            break
    return chosen


def build_days(depart: str, nights: int, activities: list[dict]) -> list[dict]:
    start = date.fromisoformat(depart)
    slots: list[list[dict]] = [[] for _ in range(nights)]
    for index, activity in enumerate(activities):
        slots[index % nights].append(activity)
    days = []
    for index, slot in enumerate(slots):
        day = start + timedelta(days=index)
        if index == nights - 1 and nights > 1:
            title = "A light last day"
        elif slot:
            title = slot[0]["area"]
        else:
            title = "Nothing booked"
        items = [item["name"] for item in slot] or ["Leave this one open. The best hours are the ones you don't schedule."]
        days.append({"label": f"{day.strftime('%a')} {day.day}", "title": title, "items": items})
    return days


def flight_options(origin_city: dict, dest_city: dict, month: int, travelers: int) -> list[dict]:
    km = haversine_km(origin_city["lat"], origin_city["lon"], dest_city["lat"], dest_city["lon"])
    pool = CARRIERS.get(dest_city.get("region", "domestic"), CARRIERS["domestic"])
    if dest_city.get("region") == "domestic":
        pool = CARRIERS["domestic"]
    salt = sum(ord(char) for char in origin_city["iata"] + dest_city["iata"])
    picked = [pool[salt % len(pool)], pool[(salt + 3) % len(pool)]]
    nonstop = fare_per_person(km, month, 0)
    later = money_round(nonstop * 1.06)
    stopped = fare_per_person(km, month, 1)
    if stopped >= nonstop:
        stopped = money_round(nonstop * 0.84)
    specs = [
        (0, picked[0], nonstop, 0, "Nonstop"),
        (1, picked[1] if picked[1] != picked[0] else picked[0], later, 0, "Nonstop"),
        (2, picked[0], stopped, 1, "1 stop"),
    ]
    delta = dest_city["lon"] - origin_city["lon"]
    while delta > 180:
        delta -= 360
    while delta < -180:
        delta += 360
    eastbound = delta > 15
    departures = [18.67, 21.5, 16.25] if eastbound else [8.25, 14.5, 7.1]
    options = []
    for variant, carrier, per_person, stops, via in specs:
        duration = max(1.4, km / 800 + 0.35) + (2.4 if stops else 0)
        depart_hour = departures[variant]
        arrive = depart_hour + duration + (approx_tz(dest_city["lon"]) - approx_tz(origin_city["lon"]))
        plus = 0
        while arrive < 0:
            arrive += 24
            plus -= 1
        plus += int(arrive // 24)
        arrive = arrive % 24
        number = 100 + (salt + variant * 97) % 800
        options.append(
            {
                "id": f"flight-{variant}",
                "carrier": carrier[0],
                "code": f"{carrier[1]} {number}",
                "depart_time": clock(depart_hour),
                "arrive_time": clock(arrive) + (f"+{plus}" if plus else ""),
                "stops": stops,
                "via": via,
                "duration": duration_label(duration),
                "price": per_person * travelers,
                "per_person": per_person,
            }
        )
    return options


def stay_options(city: dict, nights: int, travelers: int) -> list[dict]:
    stays = []
    for index, stay in enumerate(city["hotels"]):
        units = max(1, math.ceil(travelers / stay["sleeps"]))
        nightly = int(stay["nightly"])
        stays.append(
            {
                "id": f"stay-{index}",
                "name": stay["name"],
                "area": stay["area"],
                "style": stay["style"],
                "nightly": nightly,
                "nights": nights,
                "units": units,
                "total": nightly * nights * units,
                "rating": stay["rating"],
                "note": stay["note"],
            }
        )
    return stays


def choose(flights, stays, catalog_activities, meals, budget, preference, vibes, travelers):
    best = None
    for flight_index, flight in enumerate(flights):
        for stay_index, stay in enumerate(stays):
            remain = budget - flight["price"] - stay["total"] - meals
            activities = select_activities(
                catalog_activities,
                vibes,
                remain if remain > 0 else 0,
                preference,
                travelers,
            )
            act_cost = sum(item["cost"] for item in activities)
            total = flight["price"] + stay["total"] + meals + act_cost
            fits = total <= budget
            score = 200 if fits else -((total - budget) / 8)
            if preference == "cheaper":
                score += max(0, budget - total) / 25
                score -= stay["nightly"] / 8
                score -= flight["price"] / 40
            elif preference == "nicer_stay":
                score += stay["rating"] * 28
                if stay["style"] != "Hostel":
                    score += 24
                if flight["stops"] == 0:
                    score += 8
            elif preference == "more_play":
                score += len(activities) * 16
                score += sum(10 for item in activities if set(item["tags"]) & vibes)
                score += stay["rating"] * 6
                if stay["style"] == "Hostel":
                    score -= 8
                if budget and 0.72 <= total / budget <= 1:
                    score += 14
            else:
                if flight["stops"] == 0:
                    score += 36
                score += stay["rating"] * 14
                if stay["style"] == "Hostel":
                    score -= 10
                score += min(len(activities), 4) * 10
                used = total / budget if budget else 0
                if 0.68 <= used <= 1:
                    score += 28
            if len(activities) < 2:
                score -= 12
            if best is None or score > best[0]:
                best = (score, flight_index, stay_index, activities, total, fits)
    return best


def scout_lines(plan: dict) -> dict:
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    nonstops = [item for item in plan["flights"] if item["stops"] == 0]
    if not plan["fits"]:
        cheapest = min(plan["flights"], key=lambda item: item["price"])
        wing = f"Even the cheaper seat is ${cheapest['price']:,}. That is the number that breaks the budget."
    elif flight["stops"] and nonstops and nonstops[0]["price"] > flight["price"]:
        wing = (
            f"I left the ${nonstops[0]['price']:,} nonstop and took one stop "
            f"for ${flight['price']:,}, so the room still exists."
        )
    else:
        share = round(flight["price"] / plan["budget"] * 100) if plan["budget"] else 0
        wing = f"{flight['via']} on {flight['carrier']}. ${flight['price']:,} for the party, about {share}% of the budget."
    hearth = (
        f"{stay['name']} in {stay['area']}. ${stay['total']:,} for {stay['nights']} nights. {stay['note']}"
    )
    wander = (
        f"{len(plan['activities'])} plans, plus ${plan['meals']:,} in table money "
        f"(about ${plan['meal_rate']} a day, each)."
    )
    return {"wing": wing, "hearth": hearth, "wander": wander}


def diagnosis(city: dict, month: int, plan: dict, state: dict) -> str:
    if not plan["fits"]:
        pressure = "This budget doesn't clear. The docket is the cheapest version I still believe."
    elif plan["pocket"] < plan["budget"] * 0.08:
        pressure = "This budget is snug in a good way. Almost every dollar has a job."
    elif plan["pocket"] > plan["budget"] * 0.28:
        pressure = "This budget has air in it. You could upgrade the room, or eat better than I planned."
    else:
        pressure = "This budget holds the trip without squeezing the good parts out of it."
    vibe = ""
    vibes = set(state.get("vibes") or [])
    if "food" in vibes:
        vibe = " I weighted the days toward eating."
    elif "quiet" in vibes:
        vibe = " I kept the days slow."
    elif "nightlife" in vibes:
        vibe = " The evenings are doing some of the work."
    elif "museum" in vibes or "art" in vibes:
        vibe = " I left time for looking at things."
    return f"{pressure} {season_line(city, month)}{vibe}"


def docket_number(state: dict, budget: int) -> str:
    raw = f"{state['origin']}-{state['destination']}-{state['depart']}-{budget}"
    number = 1000 + (sum(ord(char) for char in raw) * 17) % 9000
    return f"LK-{number}"


def assemble(state: dict) -> dict:
    dest = destination(state["destination"])
    orig = origin(state["origin"])
    travelers = int(state["travelers"])
    nights = int(state["nights"])
    budget = int(total_budget(state) or 0)
    month = date.fromisoformat(state["depart"]).month
    # Real Google Flights and Google Hotels prices when SERPAPI_KEY is set; desk estimates otherwise.
    live_flights = live.flights(orig, dest, state["depart"], state["ret"], travelers)
    live_stays = live.stays(dest, state["depart"], state["ret"], nights, travelers)
    built_flights = live_flights or flight_options(orig, dest, month, travelers)
    built_stays = live_stays or stay_options(dest, nights, travelers)
    rate = meal_rate(state)
    meals = rate * travelers * nights
    vibes = set(state.get("vibes") or [])
    _score, flight_index, stay_index, activities, total, fits = choose(
        built_flights,
        built_stays,
        dest["activities"],
        meals,
        budget,
        state.get("preference") or "balanced",
        vibes,
        travelers,
    )
    pocket = budget - total
    plan = {
        # "google" = a live Google Flights / Google Hotels price; "desk" = Lark's estimate.
        "sources": {
            "flights": "google" if live_flights else "desk",
            "stays": "google" if live_stays else "desk",
            "activities": "desk",
        },
        "fits": fits,
        "city": dest["name"],
        "country": dest["country"],
        "origin": orig["name"],
        "origin_code": orig["iata"],
        "dest_code": dest["iata"],
        "depart": state["depart"],
        "ret": state["ret"],
        "depart_label": pretty_date(state["depart"]),
        "ret_label": pretty_date(state["ret"]),
        "nights": nights,
        "travelers": travelers,
        "budget": budget,
        "total": total,
        "pocket": pocket,
        "meals": meals,
        "meal_rate": rate,
        "docket": docket_number(state, budget),
        "dates_assumed": bool(state.get("dates_assumed")),
        "assumed_party": bool(state.get("assumed_party")),
        "flights": built_flights,
        "flight_index": flight_index,
        "stays": built_stays,
        "stay_index": stay_index,
        "activities": activities,
        "days": build_days(state["depart"], nights, activities),
        "season": season_line(dest, month),
    }
    plan["scouts"] = scout_lines(plan)
    plan["read"] = diagnosis(dest, month, plan, state)
    return plan


def pick_surprise(state: dict) -> None:
    best_slug = None
    best_score = None
    last = state.get("last_surprise")
    for slug, city in CITIES.items():
        if slug == state.get("origin"):
            continue
        trial = dict(state)
        trial["destination"] = slug
        trial["vibes"] = list(state.get("vibes") or [])
        plan = assemble(trial)
        quality = plan["stays"][plan["stay_index"]]["rating"]
        score = (1 if plan["fits"] else 0) * 100 + quality * 10 + min(len(plan["activities"]), 4)
        if slug == last:
            score -= 40
        if best_score is None or score > best_score:
            best_score = score
            best_slug = slug
    state["destination"] = best_slug
    state["last_surprise"] = best_slug
    state["surprise"] = False


def build_plan(state: dict) -> dict:
    if state.get("travelers") is None:
        state["travelers"] = 1
        state["assumed_party"] = True
    if state.get("depart") and state.get("nights") and not state.get("ret"):
        start = date.fromisoformat(state["depart"])
        state["ret"] = (start + timedelta(days=int(state["nights"]))).isoformat()
    if not state.get("destination"):
        pick_surprise(state)
    return assemble(state)
