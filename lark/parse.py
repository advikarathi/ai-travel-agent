"""Pull a trip out of plain sentences.

Lark asks one missing thing at a time, and she will not search until
there is a budget.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

from lark.catalog import ALIASES, CITIES, ORIGINS, UNSUPPORTED

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTH_RE = (
    r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
DAY_RE = r"(\d{1,2})(?:st|nd|rd|th)?"

VIBE_WORDS = {
    "food": ["food", "eat", "eating", "restaurant", "restaurants", "dinner", "hungry"],
    "walking": ["walk", "walking", "wander", "on foot"],
    "museum": ["museum", "museums", "gallery"],
    "art": ["art", "design"],
    "nightlife": ["nightlife", "bars", "party", "music", "going out"],
    "quiet": ["quiet", "calm", "slow", "relaxed", "chill"],
    "romantic": ["romantic", "honeymoon", "anniversary"],
    "adventure": ["adventure", "hike", "hiking", "outdoors"],
    "view": ["views", "view", "scenic"],
    "history": ["history", "historic", "ruins"],
}


def blank_state() -> dict:
    return {
        "origin": None,
        "destination": None,
        "depart": None,
        "ret": None,
        "nights": None,
        "travelers": None,
        "budget": None,
        "per_person": False,
        "vibes": [],
        "preference": "balanced",
        "surprise": False,
        "month_hint": None,
        "last_surprise": None,
        "unsupported": None,
        "dates_assumed": False,
    }


def fresh_state(raw: dict | None) -> dict:
    state = blank_state()
    if not raw:
        return state
    for key in state:
        if key in raw and raw[key] is not None:
            state[key] = raw[key]
    state["vibes"] = list(raw.get("vibes") or [])
    state["per_person"] = bool(raw.get("per_person"))
    state["surprise"] = bool(raw.get("surprise"))
    return state


def normalize(text: str) -> str:
    text = text.lower().replace(",", "")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("l.a.", "la")
    text = text.replace("d.c.", "dc")
    return re.sub(r"\s+", " ", text).strip()


def _upcoming(month: int, day: int, today: date | None = None) -> str | None:
    today = today or date.today()
    for year in (today.year, today.year + 1):
        try:
            found = date(year, month, day)
        except ValueError:
            continue
        if found >= today:
            return found.isoformat()
    return None


def _second_monday(year: int, month: int) -> date:
    first = date(year, month, 1)
    offset = (calendar.MONDAY - first.weekday()) % 7
    return first + timedelta(days=offset + 7)


def _suggested_depart(month: int, today: date | None = None) -> str | None:
    today = today or date.today()
    year = today.year
    if date(year, month, 1) < today.replace(day=1) or (
        month == today.month and today.day > 14
    ):
        if month < today.month or (month == today.month and today.day > 14):
            year += 1
    try:
        picked = _second_monday(year, month)
    except ValueError:
        return None
    if picked < today:
        picked = _second_monday(year + 1, month)
    return picked.isoformat()


def _set_nights(state: dict, nights: int) -> None:
    nights = max(1, min(21, nights))
    state["nights"] = nights
    if state["depart"]:
        start = date.fromisoformat(state["depart"])
        state["ret"] = (start + timedelta(days=nights)).isoformat()


def _apply_range(state: dict, start: str, end_month: int, end_day: int) -> None:
    start_date = date.fromisoformat(start)
    end = _upcoming(end_month, end_day, start_date)
    if not end:
        return
    end_date = date.fromisoformat(end)
    if end_date <= start_date:
        try:
            end_date = date(start_date.year + 1, end_month, end_day)
        except ValueError:
            return
    nights = (end_date - start_date).days
    if nights < 1 or nights > 21:
        return
    state["depart"] = start_date.isoformat()
    state["ret"] = end_date.isoformat()
    state["nights"] = nights
    state["month_hint"] = start_date.month


def find_places(text: str) -> list[tuple[int, int, str]]:
    occupied = [False] * len(text)
    found: list[tuple[int, int, str]] = []
    for alias, slug, _role in ALIASES:
        start = 0
        while True:
            index = text.find(alias, start)
            if index < 0:
                break
            end = index + len(alias)
            before_ok = index == 0 or not text[index - 1].isalpha()
            after_ok = end == len(text) or not text[end].isalnum()
            if before_ok and after_ok and not any(occupied[index:end]):
                for cursor in range(index, end):
                    occupied[cursor] = True
                found.append((index, end, slug))
            start = index + 1
    found.sort()
    return found


def leading_prep(text: str, index: int) -> str | None:
    prefix = text[max(0, index - 14) : index]
    match = re.search(r"\b(from|to|in|around|visit)\s+$", prefix)
    return match.group(1) if match else None


def extract_budget(text: str) -> tuple[int | None, bool]:
    per_person = bool(re.search(r"per person|each|a head|per head", text))
    patterns = [
        r"(?:budget(?:\s+of|\s+is)?|under|spend|around|about|max|only)\s*\$?\s*(\d+(?:\.\d+)?)\s*(k)?",
        r"\$\s*(\d+(?:\.\d+)?)\s*(k)?",
        r"\b(\d+(?:\.\d+)?)\s*k\b",
        r"\b(\d{3,6})\s*(?:dollars|usd|bucks)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        amount = float(match.group(1))
        if match.group(2):
            amount *= 1000
        if amount < 50:
            continue
        return int(round(amount)), per_person
    if re.fullmatch(r"\$?\s*\d+(?:\.\d+)?\s*k?", text):
        match = re.fullmatch(r"\$?\s*(\d+(?:\.\d+)?)\s*(k)?", text)
        if match:
            amount = float(match.group(1))
            if match.group(2):
                amount *= 1000
            if amount >= 50:
                return int(round(amount)), per_person
    return None, per_person


def extract_travelers(text: str) -> int | None:
    if re.search(r"\b(solo|alone|just me|by myself|one person)\b", text):
        return 1
    if re.search(r"\b(couple|two of us|for two|for 2|2 people|two people|we two)\b", text):
        return 2
    match = re.search(r"\bfamily of (\d+)\b", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s*(people|travelers|travellers|adults|guests)\b", text)
    if match:
        return int(match.group(1))
    if re.search(r"\bwe\b", text):
        return 2
    return None


def extract_dates(text: str, state: dict, today: date | None = None) -> None:
    today = today or date.today()
    range_match = re.search(
        rf"\b{MONTH_RE}\s+{DAY_RE}\s*(?:-|to|through)\s*(?:{MONTH_RE}\s+)?{DAY_RE}\b",
        text,
    )
    if range_match:
        start_month = MONTHS[range_match.group(1)]
        start_day = int(range_match.group(2))
        end_month_name = range_match.group(3)
        end_month = MONTHS[end_month_name] if end_month_name else start_month
        end_day = int(range_match.group(4))
        start = _upcoming(start_month, start_day, today)
        if start:
            _apply_range(state, start, end_month, end_day)
            state["dates_assumed"] = False
            return

    single = re.search(rf"\b{MONTH_RE}\s+{DAY_RE}(?!\s*(?:nights?|days?|people|travelers))\b", text)
    month_only = re.search(rf"\b(?:in|this|next|during)\s+{MONTH_RE}\b", text)
    if single:
        start = _upcoming(MONTHS[single.group(1)], int(single.group(2)), today)
        if start:
            state["depart"] = start
            state["month_hint"] = date.fromisoformat(start).month
            state["dates_assumed"] = False
    elif month_only:
        state["month_hint"] = MONTHS[month_only.group(1)]

    nights = None
    count = re.search(r"\b(\d+)\s*nights?\b", text)
    days = re.search(r"\b(\d+)\s*days?\b", text)
    if count:
        nights = int(count.group(1))
    elif days:
        nights = max(1, int(days.group(1)) - 1)
    elif re.search(r"\b(a|one)\s+week\b|\bweeklong\b", text):
        nights = 7
    elif re.search(r"\blong weekend\b", text):
        nights = 3
    elif re.search(r"\bweekend\b", text):
        nights = 2

    if re.search(r"\bnext week\b", text) and not state["depart"]:
        state["depart"] = (today + timedelta(days=7)).isoformat()
        state["month_hint"] = date.fromisoformat(state["depart"]).month
        state["dates_assumed"] = False
    elif re.search(r"\btomorrow\b", text) and not state["depart"]:
        state["depart"] = (today + timedelta(days=1)).isoformat()
        state["dates_assumed"] = False
    elif re.search(r"\bweekend\b", text) and not state["depart"] and not state["month_hint"]:
        ahead = (4 - today.weekday()) % 7
        if ahead == 0:
            ahead = 7
        state["depart"] = (today + timedelta(days=ahead)).isoformat()
        state["month_hint"] = date.fromisoformat(state["depart"]).month
        state["dates_assumed"] = False

    if nights:
        _set_nights(state, nights)
    elif state["depart"] and state["nights"]:
        _set_nights(state, int(state["nights"]))

    if state["month_hint"] and state["nights"] and not state["depart"]:
        suggested = _suggested_depart(int(state["month_hint"]), today)
        if suggested:
            state["depart"] = suggested
            _set_nights(state, int(state["nights"]))
            state["dates_assumed"] = True


def extract_vibes(text: str, state: dict) -> None:
    found = set(state["vibes"])
    for vibe, words in VIBE_WORDS.items():
        if any(re.search(rf"\b{re.escape(word)}\b", text) for word in words):
            found.add(vibe)
    state["vibes"] = sorted(found)


def extract_preference(text: str, state: dict) -> None:
    if re.search(r"\b(cheaper|cheap|tighter|less expensive|save money|make it cheaper)\b", text):
        state["preference"] = "cheaper"
    elif re.search(r"nicer (hotel|room|stay)|upgrade the (room|hotel|stay)|splurge on the (room|hotel|stay)", text):
        state["preference"] = "nicer_stay"
    elif re.search(r"\bmore food\b|food first|more to do|more going on", text):
        state["preference"] = "more_play"
    if re.search(r"\bshorter\b|fewer nights|cut (two|2) nights", text) and state["nights"] and not re.search(
        rf"\b{MONTH_RE}\s+{DAY_RE}\b", text
    ):
        _set_nights(state, max(2, int(state["nights"]) - 2))
    if re.search(r"\blonger\b|more nights|add (two|2) nights", text) and state["nights"] and not re.search(
        rf"\b{MONTH_RE}\s+{DAY_RE}\b", text
    ):
        _set_nights(state, min(21, int(state["nights"]) + 2))


def unsupported_place(text: str) -> str | None:
    for alias, label in sorted(UNSUPPORTED.items(), key=lambda item: -len(item[0])):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return label
    return None


def update_state(state: dict, message: str, today: date | None = None) -> dict:
    text = normalize(message)
    state["unsupported"] = None
    extract_preference(text, state)
    extract_vibes(text, state)

    travelers = extract_travelers(text)
    if travelers:
        state["travelers"] = max(1, min(9, travelers))
        state["assumed_party"] = False

    budget, per_person = extract_budget(text)
    if budget:
        state["budget"] = budget
        state["per_person"] = per_person
    elif per_person:
        state["per_person"] = True

    places = find_places(text)
    origin = None
    destination = None
    if len(places) >= 2:
        between = text[places[0][1] : places[1][0]]
        if re.search(r"\bto\b", between):
            origin = places[0][2]
            destination = places[1][2]
    for start, _end, slug in places:
        prep = leading_prep(text, start)
        if prep == "from":
            origin = slug
        elif prep in {"to", "in", "around", "visit"}:
            destination = slug
    if origin is None and destination is None and len(places) == 1:
        slug = places[0][2]
        prep = leading_prep(text, places[0][0])
        switching = re.search(r"\binstead\b|\brather\b|\bswitch\b", text)
        if prep == "from" or (switching and slug not in CITIES):
            origin = slug
        else:
            destination = slug
    if origin:
        state["origin"] = origin
    if destination:
        if destination in CITIES:
            state["destination"] = destination
            state["surprise"] = False
        elif destination in ORIGINS and destination not in CITIES:
            state["unsupported"] = ORIGINS[destination]["name"]
            state["destination"] = None

    if re.search(r"\b(anywhere|surprise me|you pick|your pick|you choose)\b", text):
        if not destination:
            state["surprise"] = True
            state["destination"] = None

    missing = unsupported_place(text)
    if missing and not destination:
        state["unsupported"] = missing
        state["destination"] = None

    extract_dates(text, state, today)

    if state["origin"] and state["origin"] == state["destination"]:
        state["unsupported"] = "the same city twice"
        state["destination"] = None
    return state


def total_budget(state: dict) -> int | None:
    if not state["budget"]:
        return None
    travelers = state["travelers"] or 1
    if state["per_person"]:
        return int(state["budget"]) * travelers
    return int(state["budget"])


def next_question(state: dict) -> str | None:
    if state.get("unsupported") and not state.get("destination"):
        known = ", ".join(city["name"] for city in list(CITIES.values())[:6])
        place_name = state["unsupported"]
        if place_name == "the same city twice":
            return "Pick two different cities. I can't fly you to the place you're already standing."
        return (
            f"I don't have a stay desk in {place_name} yet. "
            f"I do have {known}, and a few more if you ask."
        )
    if not state["destination"] and not state["surprise"]:
        return "Where are we going?"
    if not state["budget"]:
        if state["surprise"] and not state["destination"]:
            return (
                "I'll pick the city. First, what is the whole trip allowed to cost? "
                "One number, covering flights, the room, and the days in between."
            )
        place = "This trip"
        if state["destination"] and state["destination"] in CITIES:
            place = CITIES[state["destination"]]["name"]
        return (
            f"{place} can wait a second. What is the whole trip allowed to cost? "
            "One number, covering flights, the room, and the days in between."
        )
    if not state["origin"]:
        return "Where are you leaving from?"
    if state["per_person"] and not state["travelers"]:
        return "How many people is that budget for?"
    if state["month_hint"] and not state["nights"]:
        return f"How many nights in {calendar.month_name[int(state['month_hint'])]}?"
    if state["nights"] and not state["depart"]:
        return "When do you leave? A month is enough if you don't have the day yet."
    if state["depart"] and not state["nights"]:
        return "How many nights?"
    if not state["depart"] or not state["nights"]:
        return "When do you leave, and for how many nights?"
    return None


def suggestions_for(state: dict, ready: bool) -> list[str]:
    if ready:
        return ["Make it cheaper", "Nicer room", "More food", "Shorter"]
    if not state["destination"] and not state["surprise"]:
        return [
            "Two of us, Boston to Lisbon, 5 nights in June, $3200",
            "Solo from Chicago, a weekend in New Orleans, under $900",
            "From San Francisco to Tokyo in April, 6 nights, two people, food first, $4500",
        ]
    if not state["budget"]:
        return ["$1,500", "$3,200", "$4,500"]
    if not state["origin"]:
        return ["From Boston", "From New York", "From Chicago", "From Los Angeles"]
    if not state["depart"] or not state["nights"]:
        return ["A week in June", "Next long weekend", "5 nights in April"]
    return []
