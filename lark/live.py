"""Real flight prices from Google Flights, free, through the open-source fast-flights library.

No API key, no account: fast-flights reads the public Google Flights results page.
Lark asks for one adult's round-trip fare and multiplies by the party size.
If the library isn't installed, Google changes its page, or the lookup is slow,
Lark falls back to its own estimates and says so.

Hotels stay as estimates: there's no free, allowed source for hotel prices
(Booking.com and Airbnb don't permit scraping). The Booking.com button on the
plan opens live rates for the exact hotel and dates.

Results are cached on disk for a few hours, so a replan of the same trip is instant.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "flight_cache.json"
CACHE_HOURS = 6
TIMEOUT = 20  # seconds to wait for Google Flights before using estimates

_POOL = ThreadPoolExecutor(max_workers=2)


# ---- fetching ------------------------------------------------------------------
def _fetch(origin: str, dest: str, depart: str, ret: str):
    """Google Flights round-trip results for one adult, or None on any problem."""
    try:
        from fast_flights import FlightQuery, Passengers, create_query, get_flights
    except ImportError:
        return None
    query = create_query(
        flights=[
            FlightQuery(date=depart, from_airport=origin, to_airport=dest),
            FlightQuery(date=ret, from_airport=dest, to_airport=origin),
        ],
        trip="round-trip",
        passengers=Passengers(adults=1),
        language="en-US",
        currency="USD",
    )
    future = _POOL.submit(get_flights, query)
    try:
        return future.result(timeout=TIMEOUT)
    except FutureTimeout:
        return None
    except Exception:  # no results, a blocked request, or a changed page
        return None


def _to_plain(results) -> list[dict]:
    """fast-flights objects -> plain dicts we can cache and test."""
    plain = []
    for item in results or []:
        legs = []
        for leg in getattr(item, "flights", None) or []:
            legs.append(
                {
                    "from": leg.from_airport.code,
                    "to": leg.to_airport.code,
                    "depart_date": list(leg.departure.date),
                    "depart_time": list(leg.departure.time),
                    "arrive_date": list(leg.arrival.date),
                    "arrive_time": list(leg.arrival.time),
                    "minutes": leg.duration,
                }
            )
        plain.append({"price": item.price, "airlines": list(item.airlines or []), "legs": legs})
    return plain


def _cached_search(origin: str, dest: str, depart: str, ret: str) -> list[dict] | None:
    key = f"{origin}-{dest}-{depart}-{ret}"
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    hit = cache.get(key)
    if hit and time.time() - hit["at"] < CACHE_HOURS * 3600:
        return hit["data"]
    results = _fetch(origin, dest, depart, ret)
    if not results:
        return None
    data = _to_plain(results)
    cache[key] = {"at": time.time(), "data": data}
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass
    return data


# ---- turning Google's answer into Lark's option shape --------------------------
def _clock(hour_minute) -> str:
    hour, minute = (list(hour_minute) + [0, 0])[:2]
    suffix = "AM" if hour < 12 else "PM"
    return f"{(hour % 12) or 12}:{minute:02d} {suffix}"


def _duration(minutes: int) -> str:
    return f"{minutes // 60}h {minutes % 60:02d}m"


def parse_flights(itineraries: list[dict], travelers: int, limit: int = 5) -> list[dict]:
    options, seen = [], set()
    for itinerary in sorted(itineraries, key=lambda item: item.get("price") or 10**9):
        legs, price = itinerary.get("legs") or [], itinerary.get("price")
        if not legs or not isinstance(price, (int, float)) or price <= 0:
            continue
        first, last = legs[0], legs[-1]
        stops = len(legs) - 1
        signature = (first["depart_time"][0], first["depart_time"][1], stops, price)
        if signature in seen:
            continue
        seen.add(signature)
        # Total time, layovers included: from the first departure to the last arrival.
        minutes = sum(leg.get("minutes") or 0 for leg in legs)
        try:
            from datetime import datetime

            start = datetime(*first["depart_date"], *first["depart_time"][:2])
            end = datetime(*last["arrive_date"], *last["arrive_time"][:2])
            plus_days = (end.date() - start.date()).days
        except (TypeError, ValueError):
            plus_days = 0
        if stops:
            via = f"{stops} stop{'s' if stops > 1 else ''} via " + ", ".join(leg["to"] for leg in legs[:-1])
            # Layover time isn't in the legs; Google's elapsed time across zones isn't either,
            # so show flying time only and say so.
            duration = _duration(minutes) + " in the air"
        else:
            via = "Nonstop"
            duration = _duration(minutes)
        airlines = itinerary.get("airlines") or ["Airline"]
        per_person = int(round(price))
        options.append(
            {
                "id": f"flight-{len(options)}",
                "carrier": " + ".join(dict.fromkeys(airlines)),
                "code": "",
                "depart_time": _clock(first["depart_time"]),
                "arrive_time": _clock(last["arrive_time"]) + (f"+{plus_days}" if plus_days > 0 else ""),
                "stops": stops,
                "via": via,
                "duration": duration,
                "price": per_person * travelers,
                "per_person": per_person,
            }
        )
        if len(options) >= limit:
            break
    return options


# ---- what plan.py calls ----------------------------------------------------------
def flights(orig: dict, dest: dict, depart: str, ret: str, travelers: int) -> list[dict] | None:
    data = _cached_search(orig["iata"], dest["iata"], depart, ret)
    options = parse_flights(data, travelers) if data else []
    return options or None


def stays(dest: dict, depart: str, ret: str, nights: int, travelers: int) -> list[dict] | None:
    """No free, allowed hotel-price source: always use the estimates."""
    return None
