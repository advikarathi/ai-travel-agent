"""The destination finder, trip questions, the traveler profile, weather and Wikipedia lookups. No network."""

from __future__ import annotations

from datetime import date

import lark.extras as extras
from lark.agent import respond

TODAY = date(2026, 11, 9)
LISBON = "Two of us, Boston to Lisbon, 5 nights in June, $3200"


# ---- where can I go? --------------------------------------------------------------
def test_llm_picks_the_city_and_says_why(fake_llm):
    result = respond("Where can we go from Boston for $2500 in April? Two of us, 5 nights, food", today=TODAY)
    plan = result["plan"]
    assert [task for task, _ in fake_llm.calls] == ["extract", "destination", "plan"]
    candidates = fake_llm.calls[1][1]["candidates"]
    assert len(candidates) == 10 and all("estimated_total" in c for c in candidates)
    pick = plan["destination_pick"]
    assert pick["by"] == "llm" and plan["city"] in pick["why"]
    assert len(pick["compared"]) == 10
    assert result["reply"].startswith("You asked me to choose, so I picked " + plan["city"])


def test_comparing_cities_never_looks_up_live_fares(monkeypatch, fake_llm):
    import lark.live

    calls = []
    monkeypatch.setattr(lark.live, "flights", lambda *a: calls.append(a[1]["iata"]) or None)
    respond("Surprise me from Boston, $3000, a week in May, two of us", today=TODAY)
    assert len(calls) == 1  # only the chosen city gets a live lookup


def test_bad_city_pick_falls_back_to_rules(fake_llm):
    fake_llm.destination_override = {"slug": "atlantis", "why": "Nice."}
    plan = respond("Surprise me from Boston, $3000, a week in May, two of us", today=TODAY)["plan"]
    assert plan["destination_pick"]["by"] == "rules" and plan["city"]


# ---- questions about the trip on screen ------------------------------------------------
def test_question_about_the_plan_is_answered_without_replanning(fake_llm):
    first = respond(LISBON, today=TODAY)
    fake_llm.extract_override = {"intent": "question"}
    fake_llm.calls.clear()
    answer = respond("What should I pack?", first["state"], today=TODAY, current_plan=first["plan"])
    assert answer["status"] == "answered" and answer["plan"] is None
    assert "Lisbon" in answer["reply"]
    assert [task for task, _ in fake_llm.calls] == ["extract", "answer"]
    brief = fake_llm.calls[1][1]["plan"]
    assert brief["stay"]["name"] and brief["days"]
    assert answer["state"]["destination"] == first["state"]["destination"]


def test_change_requests_still_replan(fake_llm):
    first = respond(LISBON, today=TODAY)
    again = respond("Make it cheaper", first["state"], today=TODAY, current_plan=first["plan"])
    assert again["status"] == "ready" and again["plan"]


# ---- profile and weather reach the planner ---------------------------------------------
def test_profile_and_weather_go_to_the_model(monkeypatch, fake_llm):
    monkeypatch.setattr(
        extras, "weather",
        lambda lat, lon, depart, nights, today=None: [
            {"date": "x", "high": 70, "low": 58, "summary": "Rain", "rain_chance": 80, "rain_mm": None, "wet": True, "kind": "forecast"}
        ] * nights,
    )
    state = {"profile": {"pace": "relaxed", "walking": "minimal", "diet": "vegetarian"}}
    plan = respond(LISBON, state, today=TODAY)["plan"]
    payload = [p for task, p in fake_llm.calls if task == "plan"][0]
    assert payload["trip"]["profile"]["diet"] == "vegetarian"
    assert payload["weather"][0]["wet"] is True and payload["weather_kind"] == "forecast"
    assert len(plan["weather"]) == plan["nights"]


# ---- the free lookups themselves -------------------------------------------------------
def test_open_meteo_days_are_read_and_rain_flagged():
    data = {"daily": {"time": ["2027-06-14", "2027-06-15"], "temperature_2m_max": [78.4, 69.2],
                      "temperature_2m_min": [61.0, 59.9], "precipitation_probability_max": [10, 70],
                      "weather_code": [1, 61]}}
    days = extras.parse_weather(data, "forecast")
    assert days[0] == {"date": "2027-06-14", "high": 78, "low": 61, "summary": "Partly cloudy",
                       "rain_chance": 10, "rain_mm": None, "wet": False, "kind": "forecast"}
    assert days[1]["summary"] == "Rain" and days[1]["wet"] is True


def test_wikipedia_result_must_match_the_name_and_be_near():
    lisbon = (38.77, -9.13)
    pages = [
        {"title": "Belém Tower", "coordinates": [{"lat": 38.69, "lon": -9.21}], "thumbnail": {"source": "x.jpg"}},
        {"title": "Pastéis de Belém", "coordinates": [{"lat": 38.697, "lon": -9.203}], "thumbnail": {"source": "tart.jpg"}},
    ]
    # Both share "Belém"; the bakery covers the whole name, so it wins over the tower next door.
    assert extras.best_page(pages, "Pastéis de Belém", *lisbon)["title"] == "Pastéis de Belém"
    near = [{"title": "Pena Palace", "coordinates": [{"lat": 38.79, "lon": -9.39}], "thumbnail": {"source": "p.jpg"}}]
    assert extras.best_page(near, "Sintra and Pena", *lisbon)["photo"] == "p.jpg"
    far = [{"title": "Pena Palace", "coordinates": [{"lat": 40.0, "lon": -3.7}], "thumbnail": {"source": "p.jpg"}}]
    assert extras.best_page(far, "Sintra and Pena", *lisbon) is None
    unrelated = [{"title": "Lisbon", "coordinates": [{"lat": 38.72, "lon": -9.14}]}]
    assert extras.best_page(unrelated, "Tram 28, early", *lisbon) is None


def test_lookups_fail_quietly():
    # conftest blocks the network: everything comes back empty, nothing raises.
    assert extras.weather(38.77, -9.13, "2027-06-14", 5, today=TODAY) == []
    assert extras.place("Colosseum", "Rome", 41.8, 12.25) is None
    assert extras.city_photo("Rome") is None


# ---- exports ---------------------------------------------------------------------
def test_calendar_and_pdf_exports():
    from lark import export

    plan = respond(LISBON, today=TODAY)["plan"]
    ics = export.to_ics(plan).decode("utf-8")
    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.rstrip().endswith("END:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == plan["nights"] + 2
    assert f"DTSTART;VALUE=DATE:{plan['depart'].replace('-', '')}" in ics
    pdf = export.to_pdf(plan)
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500
