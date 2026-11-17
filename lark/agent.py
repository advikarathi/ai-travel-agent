"""The desk agent. She asks for a budget before anyone goes looking.

The LLM does two jobs on every turn:
  1. read the message and turn it into trip fields (extract_with_llm)
  2. choose a flight, a stay, and activities from the desk inventory and
     write the day-by-day plan plus the trade-offs (plan_with_llm)

The rule-based parser and planner still run underneath. They fill gaps the
model leaves, generate the priced options it chooses from, and re-check its
choice, so every dollar amount comes from the inventory, never the model.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from lark import extras
from lark.catalog import ALIASES, CITIES, ORIGINS, destination
from lark.llm import LLMBadOutput, get_llm
from lark.parse import (
    VIBE_WORDS,
    _suggested_depart,
    find_places,
    fresh_state,
    next_question,
    normalize,
    suggestions_for,
    update_state,
)
from lark.plan import activity_cost, build_days, build_plan, destination_candidates, diagnosis, scout_lines

PREFERENCES = {"balanced", "cheaper", "nicer_stay", "more_play"}

EXTRACT_SYSTEM = """You are the intake desk of Lark, a budget-first trip planner.
Read the traveler's latest message, using trip_so_far for context, and return the trip fields
this message sets or changes. Use null for anything the message does not mention. Never guess
a budget or a destination the traveler did not give.

Return exactly these keys:
  "origin": city they leave from, or null
  "destination": city they want to visit, or null (any city, even one not in known_destinations)
  "surprise": true only if they ask you to pick the destination
  "depart": departure date as YYYY-MM-DD (must be on or after today), or null
  "nights": integer number of nights, or null. "a week" = 7, "long weekend" = 3, "weekend" = 2,
            "5 days" = 4. For "shorter"/"longer" adjust trip_so_far.nights by 2.
  "month": month number 1-12 if they name a month but no exact day, else null
  "budget": whole-trip budget in USD as an integer, or null
  "per_person": true if the budget is per person
  "travelers": integer head count, or null. "couple"/"two of us" = 2, "solo" = 1
  "vibes": list drawn only from vibe_options, [] if none
  "preference": one of "cheaper", "nicer_stay", "more_play", "balanced", or null if unchanged
  "intent": "question" if has_plan is true and the message only asks something about that trip
            (packing, weather, timing, why a choice was made) without asking to change it;
            otherwise "plan"
"""

PLAN_SYSTEM = """You are the planner of Lark, a budget-first trip desk.
Pick ONE flight, ONE stay, and the activities that best fit the traveler's budget and vibes,
using only the ids given in options. Prices are already computed for the whole party, so:
  total = flight.price + stay.total + meals + sum(activity.cost)
and total must stay at or under budget whenever any combination allows it. Prefer leaving a
little money spare over spending every dollar, unless preference says otherwise. A one-stop
flight that frees money for a better stay or more activities is a fair trade; say so.

Return exactly these keys:
  "flight_id": an id from options.flights
  "stay_id": an id from options.stays
  "activity_ids": 2-6 ids from options.activities
  "days": a list with exactly one entry per date in dates, each
          {"title": short theme for the day, "activity_ids": ids from your activity_ids,
           "note": one sentence of free-time advice (no new paid bookings, no prices)}
          Use every chosen activity exactly once. Keep the last day light.
          If weather is given, put outdoor activities on dry days and museums, food and
          indoor picks on wet ones, and mention the weather in that day's note.
          Respect profile when given: pace "relaxed" = at most one paid activity a day,
          "packed" = fill the days; walking "minimal" = skip walking-heavy picks;
          diet = suit food picks and notes to it.
  "tradeoffs": 2-4 plain sentences on what you traded and why (e.g. cheaper flight vs better
               room, which vibe got the most time, what was left out). Quote only prices from options."""

DESTINATION_SYSTEM = """You are the destination desk of Lark, a budget-first trip planner.
The traveler has not picked a city. Each candidate is already priced for their exact party,
dates and nights on Lark's estimates. Choose the ONE city that best fits: it should fit the
budget if any city does; then weigh season ("best" beats "okay" beats "tough") and how many
activities match their vibes. Avoid previous_pick unless it is clearly the best fit.

Return exactly these keys:
  "slug": the chosen candidate's slug
  "why": 2-3 plain sentences on why this city, quoting only estimated totals from candidates
  "runner_up": another candidate's slug, or null"""

ANSWER_SYSTEM = """You are Lark, a budget-first trip planner. The traveler already has the plan below
and is asking a question about it. Answer from the plan (flight, stay, days, budget, weather,
profile) plus general travel knowledge. Use 2-5 short, specific sentences in plain words.
Quote only prices that appear in the plan; never invent prices, opening hours or bookings.
If they really want the plan changed, say what to type (for example "make it cheaper").

Return exactly one key:
  "answer": your answer as plain text"""


def _place_slug(name: object) -> str | None:
    if not isinstance(name, str) or not name.strip():
        return None
    text = normalize(name)
    for alias, slug, _role in ALIASES:
        if alias == text:
            return slug
    found = find_places(text)
    return found[0][2] if found else None


def _int(value: object, low: int, high: int) -> int | None:
    try:
        number = int(round(float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if low <= number <= high else None


def _trip_summary(state: dict) -> dict:
    def name(slug: str | None) -> str | None:
        place = ORIGINS.get(slug or "") or CITIES.get(slug or "")
        return place["name"] if place else None

    return {
        "origin": name(state.get("origin")),
        "destination": name(state.get("destination")),
        "depart": state.get("depart"),
        "nights": state.get("nights"),
        "budget": state.get("budget"),
        "per_person": state.get("per_person"),
        "travelers": state.get("travelers"),
        "vibes": state.get("vibes"),
        "preference": state.get("preference"),
    }


def extract_with_llm(llm, message: str, before: dict, state: dict, today: date, has_plan: bool = False) -> dict:
    """Ask the model for trip fields and lay them over the rule-based parse. Returns the raw fields."""
    fields = llm.chat_json(
        "extract",
        EXTRACT_SYSTEM,
        {
            "today": today.isoformat(),
            "message": message,
            "trip_so_far": _trip_summary(before),
            "known_destinations": [city["name"] for city in CITIES.values()],
            "vibe_options": sorted(VIBE_WORDS),
            "has_plan": has_plan,
        },
    )
    if fields.get("intent") == "question" and has_plan:
        return fields  # a question about the trip: leave the trip as it is

    origin_slug = _place_slug(fields.get("origin"))
    if origin_slug and origin_slug in ORIGINS:
        state["origin"] = origin_slug

    dest_name = fields.get("destination")
    dest_slug = _place_slug(dest_name)
    if dest_slug in CITIES:
        state["destination"] = dest_slug
        state["surprise"] = False
        state["unsupported"] = None
    elif isinstance(dest_name, str) and dest_name.strip():
        state["destination"] = None
        state["unsupported"] = ORIGINS[dest_slug]["name"] if dest_slug else dest_name.strip().title()
    elif fields.get("surprise") is True:
        state["surprise"] = True
        state["destination"] = None

    budget = _int(fields.get("budget"), 50, 500_000)
    if budget:
        state["budget"] = budget
        state["per_person"] = bool(fields.get("per_person"))
    elif fields.get("per_person") is True:
        state["per_person"] = True

    travelers = _int(fields.get("travelers"), 1, 9)
    if travelers:
        state["travelers"] = travelers
        state["assumed_party"] = False

    vibes = [vibe for vibe in fields.get("vibes") or [] if vibe in VIBE_WORDS]
    if vibes:
        state["vibes"] = sorted(set(state["vibes"]) | set(vibes))

    if fields.get("preference") in PREFERENCES:
        state["preference"] = fields["preference"]

    nights = _int(fields.get("nights"), 1, 21)
    depart = fields.get("depart")
    try:
        depart_date = date.fromisoformat(depart) if isinstance(depart, str) else None
    except ValueError:
        depart_date = None
    if depart_date and depart_date >= today:
        state["depart"] = depart_date.isoformat()
        state["month_hint"] = depart_date.month
        state["dates_assumed"] = False
    month = _int(fields.get("month"), 1, 12)
    if month and not depart_date:
        state["month_hint"] = month
        if state.get("depart") and date.fromisoformat(state["depart"]).month != month:
            state["depart"] = None
    if nights:
        state["nights"] = nights
    if state["month_hint"] and state["nights"] and not state["depart"]:
        suggested = _suggested_depart(int(state["month_hint"]), today)
        if suggested:
            state["depart"] = suggested
            state["dates_assumed"] = True
    if state["depart"] and state["nights"]:
        state["ret"] = (date.fromisoformat(state["depart"]) + timedelta(days=int(state["nights"]))).isoformat()

    if state["origin"] and state["origin"] == state["destination"]:
        state["unsupported"] = "the same city twice"
        state["destination"] = None
    return fields


def _activity_options(plan: dict, state: dict) -> list[dict]:
    city = destination(state["destination"])
    travelers = int(plan["travelers"])
    return [
        {
            "id": f"act-{index}",
            "name": item["name"],
            "area": item["area"],
            "cost": activity_cost(item, travelers),
            "hours": item["hours"],
            "tags": list(item["tags"]),
            "note": item["note"],
        }
        for index, item in enumerate(city["activities"])
    ]


def plan_with_llm(llm, state: dict, plan: dict) -> dict:
    """Let the model choose from the priced options, then audit the choice in code.

    Returns the plan, updated with the model's choice when it holds up.
    """
    activities = _activity_options(plan, state)
    start = date.fromisoformat(plan["depart"])
    dates = [(start + timedelta(days=offset)).strftime("%a %b %d") for offset in range(plan["nights"])]
    pick = llm.chat_json(
        "plan",
        PLAN_SYSTEM,
        {
            "trip": {
                "from": plan["origin"],
                "to": f"{plan['city']}, {plan['country']}",
                "travelers": plan["travelers"],
                "nights": plan["nights"],
                "season": plan["season"],
                "budget": plan["budget"],
                "meals": plan["meals"],
                "vibes": state.get("vibes") or [],
                "preference": state.get("preference") or "balanced",
                "profile": state.get("profile") or {},
            },
            "dates": dates,
            "weather": [
                {"date": day["date"], "summary": day["summary"], "high_f": day["high"], "low_f": day["low"], "wet": day["wet"]}
                for day in plan.get("weather") or []
            ],
            "weather_kind": (plan.get("weather") or [{}])[0].get("kind"),
            "options": {
                "flights": [
                    {key: flight[key] for key in ("id", "carrier", "via", "duration", "depart_time", "price")}
                    for flight in plan["flights"]
                ],
                "stays": [
                    {key: stay[key] for key in ("id", "name", "area", "style", "rating", "nightly", "total", "note")}
                    for stay in plan["stays"]
                ],
                "activities": activities,
            },
        },
    )

    flight_ids = [flight["id"] for flight in plan["flights"]]
    stay_ids = [stay["id"] for stay in plan["stays"]]
    by_id = {item["id"]: item for item in activities}
    if pick.get("flight_id") not in flight_ids or pick.get("stay_id") not in stay_ids:
        raise LLMBadOutput("The model picked a flight or stay that isn't in the inventory.")
    chosen_ids: list[str] = []
    for item in pick.get("activity_ids") or []:
        if item in by_id and item not in chosen_ids:
            chosen_ids.append(item)

    flight = plan["flights"][flight_ids.index(pick["flight_id"])]
    stay = plan["stays"][stay_ids.index(pick["stay_id"])]
    fixed = flight["price"] + stay["total"] + plan["meals"]

    # The model proposes, the ledger disposes: trim the priciest extras until it fits.
    dropped = []
    while chosen_ids and fixed + sum(by_id[i]["cost"] for i in chosen_ids) > plan["budget"]:
        priciest = max(chosen_ids, key=lambda i: by_id[i]["cost"])
        if by_id[priciest]["cost"] == 0:
            break
        chosen_ids.remove(priciest)
        dropped.append(by_id[priciest]["name"])
    total = fixed + sum(by_id[i]["cost"] for i in chosen_ids)
    fits = total <= plan["budget"]

    if not fits and plan["fits"]:
        plan["chosen_by"] = "rules"
        plan["tradeoffs"] = (
            "The model's pick ran over budget even after trimming, so this is the rule-based pick instead."
        )
        return plan

    chosen = [
        {key: by_id[i][key] for key in ("name", "area", "cost", "note", "tags")} for i in chosen_ids
    ]
    plan.update(
        {
            "flight_index": flight_ids.index(flight["id"]),
            "stay_index": stay_ids.index(stay["id"]),
            "activities": chosen,
            "total": total,
            "pocket": plan["budget"] - total,
            "fits": fits,
            "chosen_by": "llm",
        }
    )

    days = pick.get("days")
    if isinstance(days, list) and len(days) == plan["nights"] and not dropped:
        built = []
        for offset, day in enumerate(days):
            day = day if isinstance(day, dict) else {}
            when = start + timedelta(days=offset)
            items = [by_id[i]["name"] for i in day.get("activity_ids") or [] if i in chosen_ids]
            note = str(day.get("note") or "").strip()
            if note:
                items.append(note)
            built.append(
                {
                    "label": f"{when.strftime('%a')} {when.day}",
                    "title": str(day.get("title") or "Free day").strip()[:60],
                    "items": items or ["Leave this one open."],
                }
            )
        plan["days"] = built
    else:
        plan["days"] = build_days(plan["depart"], plan["nights"], chosen)

    raw = pick.get("tradeoffs") or ""
    # Some models send the sentences as a list; join them into one paragraph.
    if isinstance(raw, (list, tuple)):
        raw = " ".join(str(part).strip() for part in raw if str(part).strip())
    tradeoffs = str(raw).strip()
    if dropped:
        tradeoffs += f" I cut {', '.join(dropped)} to stay inside the budget."
    plan["tradeoffs"] = tradeoffs.strip()
    plan["scouts"] = scout_lines(plan)
    month = date.fromisoformat(plan["depart"]).month
    plan["read"] = diagnosis(destination(state["destination"]), month, plan, state)
    return plan


def choose_destination_with_llm(llm, state: dict, candidates: list[dict]) -> tuple[str, str, str | None]:
    """The model picks the city from priced candidates. Returns (slug, why, runner_up)."""
    pick = llm.chat_json(
        "destination",
        DESTINATION_SYSTEM,
        {
            "trip": {
                "from": ORIGINS[state["origin"]]["name"] if state.get("origin") in ORIGINS else None,
                "depart": state.get("depart"),
                "nights": state.get("nights"),
                "travelers": state.get("travelers"),
                "budget": state.get("budget"),
                "vibes": state.get("vibes") or [],
                "profile": state.get("profile") or {},
            },
            "previous_pick": state.get("last_surprise"),
            "candidates": [{key: value for key, value in row.items() if key != "country"} for row in candidates],
        },
    )
    slugs = [row["slug"] for row in candidates]
    if pick.get("slug") not in slugs:
        raise LLMBadOutput("The model picked a city that isn't a candidate.")
    runner = pick.get("runner_up") if pick.get("runner_up") in slugs and pick.get("runner_up") != pick["slug"] else None
    why = pick.get("why") or ""
    if isinstance(why, (list, tuple)):
        why = " ".join(str(part).strip() for part in why)
    return pick["slug"], str(why).strip(), runner


def plan_brief(plan: dict, state: dict) -> dict:
    """What the model needs to answer questions about a plan."""
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    return {
        "from": plan["origin"],
        "to": f"{plan['city']}, {plan['country']}",
        "dates": f"{plan['depart_label']} to {plan['ret_label']} ({plan['nights']} nights)",
        "travelers": plan["travelers"],
        "budget": plan["budget"],
        "estimated_total": plan["total"],
        "left_over": plan["pocket"],
        "flight": {k: flight.get(k) for k in ("carrier", "via", "duration", "depart_time", "arrive_time", "price")},
        "flight_price_source": (plan.get("sources") or {}).get("flights"),
        "stay": {k: stay.get(k) for k in ("name", "area", "style", "rating", "nightly", "total")},
        "meals": plan["meals"],
        "activities": [{k: a.get(k) for k in ("name", "area", "cost", "note")} for a in plan["activities"]],
        "days": [{"day": d["label"], "title": d["title"], "items": d["items"]} for d in plan["days"]],
        "weather": plan.get("weather") or [],
        "season": plan.get("season"),
        "profile": state.get("profile") or {},
        "why_this_plan": plan.get("tradeoffs"),
    }


def answer_question(llm, question: str, plan: dict, state: dict) -> str:
    reply = llm.chat_json("answer", ANSWER_SYSTEM, {"question": question, "plan": plan_brief(plan, state)})
    answer = reply.get("answer")
    if isinstance(answer, (list, tuple)):
        answer = " ".join(str(part) for part in answer)
    answer = str(answer or "").strip()
    if not answer:
        raise LLMBadOutput("The model returned an empty answer.")
    return answer


def _looks_like_question(text: str) -> bool:
    text = text.strip().lower()
    return text.endswith("?") or bool(re.match(r"^(what|why|how|when|which|is|are|do|does|should|can|will)\b", text))


def narrate(state: dict, plan: dict) -> str:
    city = plan["city"]
    budget = f"${plan['budget']:,}"
    if plan["fits"]:
        line = (
            f"{city} for {plan['travelers']}, {plan['nights']} nights, {budget}. "
            f"It clears with ${plan['pocket']:,} still in your pocket."
        )
    else:
        gap = plan["total"] - plan["budget"]
        line = (
            f"I ran {city} honestly. The cheapest version I trust is ${plan['total']:,}, "
            f"which is ${gap:,} over {budget}. The docket shows that version. "
            "Add money, or say shorter."
        )
    if plan.get("dates_assumed"):
        line += f" I put you down for {plan['depart_label']} to {plan['ret_label']}. Move it if that's the wrong week."
    if plan.get("assumed_party"):
        line += " I planned this for one person."
    if state.get("_surprised"):
        line = f"You asked me to choose, so I picked {city}. " + line
    sources = plan.get("sources") or {}
    if sources.get("flights") == "google":
        line += " The flight price is live from Google Flights; hotel and activity prices are estimates."
    else:
        line += " Prices are estimates (Google Flights didn't answer, so I used my own)."
    return line


def respond(
    message: str, state: dict | None = None, today: date | None = None, current_plan: dict | None = None
) -> dict:
    """One turn of the desk. Raises lark.llm.LLMError subclasses the UI should show.

    current_plan: the plan already on screen, so questions about it can be answered.
    """
    llm = get_llm()
    today = today or date.today()
    current = fresh_state(state)
    before = dict(current)
    notes: list[str] = []
    text = message or ""
    fields: dict = {}
    update_state(current, text, today)
    if text.strip():
        try:
            fields = extract_with_llm(llm, text, before, current, today, has_plan=bool(current_plan))
        except LLMBadOutput:
            notes.append("The model's reading of that message was unusable, so I parsed it by rule.")

    # A question about the trip on screen: answer it, change nothing.
    unchanged = all(current.get(k) == before.get(k) for k in ("destination", "budget", "nights", "depart", "travelers", "origin", "preference"))
    if current_plan and text.strip() and (fields.get("intent") == "question" or (not fields and unchanged and _looks_like_question(text))):
        try:
            answer = answer_question(llm, text, current_plan, before)
        except LLMBadOutput:
            answer = "I couldn't put together an answer to that. Try asking it another way."
        return {"reply": answer, "state": fresh_state(before), "plan": None, "suggestions": [], "status": "answered", "notes": notes}

    question = next_question(current)
    if question:
        return {
            "reply": question,
            "state": current,
            "plan": None,
            "suggestions": suggestions_for(current, ready=False),
            "status": "asking",
            "notes": notes,
        }

    surprised = bool(current.get("surprise") and not current.get("destination"))
    pick_note = None
    if surprised:
        # Same set-up build_plan does, so every city is priced for this exact trip.
        if current.get("travelers") is None:
            current["travelers"] = 1
            current["assumed_party"] = True
        if not current.get("ret"):
            current["ret"] = (date.fromisoformat(current["depart"]) + timedelta(days=int(current["nights"]))).isoformat()
        candidates = destination_candidates(current)
        try:
            slug, why, runner = choose_destination_with_llm(llm, current, candidates)
            current.update(destination=slug, last_surprise=slug, surprise=False)
            pick_note = {"by": "llm", "why": why, "runner_up": CITIES[runner]["name"] if runner else None}
        except LLMBadOutput:
            pick_note = {"by": "rules", "why": "I compared every city on estimated prices and picked the best fit by rule.", "runner_up": None}
        pick_note["compared"] = [
            {"city": row["city"], "estimated_total": row["estimated_total"], "fits": row["fits"], "season": row["season"]}
            for row in candidates
        ]
    plan = build_plan(current)
    city = destination(current["destination"])
    plan["lat"], plan["lon"] = city["lat"], city["lon"]
    plan["weather"] = extras.weather(city["lat"], city["lon"], plan["depart"], plan["nights"], today=today)
    if pick_note:
        plan["destination_pick"] = pick_note
    current["_surprised"] = surprised
    try:
        plan = plan_with_llm(llm, current, plan)
    except LLMBadOutput:
        plan["chosen_by"] = "rules"
        plan["tradeoffs"] = ""
        notes.append("The model's plan didn't match the inventory, so this is the rule-based pick.")

    reply = narrate(current, plan)
    if plan.get("tradeoffs"):
        reply += "\n\n" + plan["tradeoffs"]
    current.pop("_surprised", None)
    return {
        "reply": reply,
        "state": current,
        "plan": plan,
        "suggestions": suggestions_for(current, ready=True),
        "status": "ready",
        "notes": notes,
    }
