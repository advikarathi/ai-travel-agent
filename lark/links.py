"""Links that let a person check every estimate against the real thing.

Lark's prices are desk estimates. These links open live searches for the exact
route, dates, party size and place, so the plan can be verified and booked.
No API keys: they are ordinary public search URLs.
"""

from __future__ import annotations

from urllib.parse import urlencode


def maps(query: str) -> str:
    """A Google Maps search for a place (the documented Maps URLs format)."""
    return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": query})


def google_flights(plan: dict) -> str:
    query = (
        f"Flights from {plan['origin_code']} to {plan['dest_code']} on {plan['depart']} "
        f"through {plan['ret']} for {plan['travelers']} adults"
    )
    return "https://www.google.com/travel/flights?" + urlencode({"q": query})


def kayak(plan: dict) -> str:
    party = f"/{plan['travelers']}adults" if plan["travelers"] > 1 else ""
    return (
        f"https://www.kayak.com/flights/{plan['origin_code']}-{plan['dest_code']}"
        f"/{plan['depart']}/{plan['ret']}{party}"
    )


def booking(stay: dict, plan: dict) -> str:
    params = {
        "ss": f"{stay['name']}, {plan['city']}",
        "checkin": plan["depart"],
        "checkout": plan["ret"],
        "group_adults": plan["travelers"],
        "no_rooms": stay.get("units") or 1,
    }
    return "https://www.booking.com/searchresults.html?" + urlencode(params)


def place(name: str, area: str, plan: dict) -> str:
    return maps(f"{name}, {area}, {plan['city']}, {plan['country']}")
