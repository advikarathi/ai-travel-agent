"""Live flight prices: shaping fast-flights results, and the planner using them. No network."""

from __future__ import annotations

from datetime import date

import lark.live
from fast_flights.model import Airport, CarbonEmission, Flights, SimpleDatetime, SingleFlight
from lark.agent import respond

TODAY = date(2026, 11, 9)


def leg(frm, to, d1, t1, d2, t2, minutes):
    return SingleFlight(
        from_airport=Airport(name=frm, code=frm),
        to_airport=Airport(name=to, code=to),
        departure=SimpleDatetime(date=d1, time=t1),
        arrival=SimpleDatetime(date=d2, time=t2),
        duration=minutes,
        plane_type="A321neo",
    )


# The real result types from fast-flights 3.1, filled the way Google answers for BOS-LIS.
RESULTS = [
    Flights(type="TP", price=742, airlines=["TAP Air Portugal"], carbon=CarbonEmission(0, 0),
            flights=[leg("BOS", "LIS", (2027, 6, 14), (21, 5), (2027, 6, 15), (8, 40), 395)]),
    Flights(type="multi", price=655, airlines=["Delta"], carbon=CarbonEmission(0, 0),
            flights=[leg("BOS", "JFK", (2027, 6, 14), (17, 30), (2027, 6, 14), (18, 45), 75),
                     leg("JFK", "LIS", (2027, 6, 14), (21, 10), (2027, 6, 15), (9, 5), 415)]),
    Flights(type="TP", price=742, airlines=["TAP Air Portugal"], carbon=CarbonEmission(0, 0),  # duplicate
            flights=[leg("BOS", "LIS", (2027, 6, 14), (21, 5), (2027, 6, 15), (8, 40), 395)]),
]


def test_results_become_party_fares_cheapest_first():
    options = lark.live.parse_flights(lark.live._to_plain(RESULTS), travelers=2)
    assert [o["carrier"] for o in options] == ["Delta", "TAP Air Portugal"]  # duplicate dropped
    connecting, nonstop = options
    assert nonstop["price"] == 742 * 2 and nonstop["per_person"] == 742
    assert nonstop["via"] == "Nonstop" and nonstop["duration"] == "6h 35m"
    assert nonstop["depart_time"] == "9:05 PM" and nonstop["arrive_time"] == "8:40 AM+1"
    assert connecting["via"] == "1 stop via JFK" and connecting["stops"] == 1


def test_planner_uses_google_flights_when_it_answers(monkeypatch):
    monkeypatch.setattr(lark.live, "CACHE", lark.live.ROOT / "data" / "_test_cache_unused.json")
    monkeypatch.setattr(lark.live, "_cached_search", lambda *a: lark.live._to_plain(RESULTS))
    result = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)
    plan = result["plan"]
    assert plan["sources"]["flights"] == "google" and plan["sources"]["stays"] == "desk"
    flight = plan["flights"][plan["flight_index"]]
    assert flight["price"] in {742 * 2, 655 * 2}
    assert plan["total"] == flight["price"] + plan["stays"][plan["stay_index"]]["total"] + plan["meals"] + sum(
        a["cost"] for a in plan["activities"]
    )
    assert "live from Google Flights" in result["reply"]


def test_no_answer_means_estimates_and_says_so():
    result = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)
    assert result["plan"]["sources"]["flights"] == "desk"
    assert "estimates" in result["reply"]


def test_cache_means_one_lookup_per_trip(monkeypatch, tmp_path):
    monkeypatch.setattr(lark.live, "CACHE", tmp_path / "cache.json")
    calls = []
    monkeypatch.setattr(lark.live, "_fetch", lambda *a: calls.append(a) or RESULTS)
    first = lark.live._cached_search("BOS", "LIS", "2027-06-14", "2027-06-19")
    second = lark.live._cached_search("BOS", "LIS", "2027-06-14", "2027-06-19")
    assert first == second and len(calls) == 1
