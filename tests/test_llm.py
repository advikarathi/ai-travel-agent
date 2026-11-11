from datetime import date

import pytest

import lark.agent
from lark.agent import respond
from lark.llm import LLMNotConfigured, LLMRateLimited, get_llm, parse_json
from lark.storage import load_trips, save_trip

TODAY = date(2026, 11, 9)


def test_llm_extraction_fills_what_regex_misses(fake_llm):
    # The regex parser can't read "the city of light" or "thirty-two hundred bucks".
    fake_llm.extract_override = {
        "origin": "Boston",
        "destination": "Paris",
        "depart": "2027-05-10",
        "nights": 5,
        "budget": 3200,
        "travelers": 2,
        "vibes": ["museum", "made-up-vibe"],
    }
    result = respond("me and my partner, city of light, from beantown, mid may, thirty-two hundred bucks", today=TODAY)
    plan = result["plan"]
    assert plan["city"] == "Paris"
    assert plan["budget"] == 3200 and plan["travelers"] == 2 and plan["nights"] == 5
    assert plan["depart"] == "2027-05-10" and plan["ret"] == "2027-05-15"
    assert result["state"]["vibes"] == ["museum"]
    assert [task for task, _ in fake_llm.calls] == ["extract", "plan"]


def test_llm_unknown_destination_is_refused(fake_llm):
    fake_llm.extract_override = {"destination": "Kathmandu"}
    result = respond("I want to see Everest base camp", today=TODAY)
    assert result["plan"] is None
    assert "Kathmandu" in result["reply"]


def test_llm_pick_is_used_and_priced_by_the_inventory(fake_llm):
    result = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)
    plan = result["plan"]
    assert plan["chosen_by"] == "llm"
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    assert plan["total"] == flight["price"] + stay["total"] + plan["meals"] + sum(a["cost"] for a in plan["activities"])
    assert len(plan["days"]) == 5
    assert "cheapest seat" in result["reply"]


def test_overbudget_llm_pick_gets_trimmed(fake_llm):
    fake_llm.plan_override = {
        "flight_id": "flight-0",
        "stay_id": "stay-3",
        "activity_ids": ["act-0", "act-1", "act-2", "act-3", "act-4", "act-5"],
        "days": [],
        "tradeoffs": "Everything.",
    }
    result = respond("Solo from Chicago, a weekend in New Orleans, under $900", today=TODAY)
    plan = result["plan"]
    assert plan["total"] <= 900
    assert "cut" in plan["tradeoffs"] or plan["chosen_by"] == "rules"


def test_invented_ids_fall_back_to_rules(fake_llm):
    fake_llm.plan_override = {"flight_id": "flight-99", "stay_id": "The Ritz", "activity_ids": []}
    result = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)
    assert result["plan"]["chosen_by"] == "rules"
    assert result["plan"]["fits"] is True
    assert result["notes"]


def test_rate_limit_reaches_the_caller(fake_llm):
    def limited(*_args):
        raise LLMRateLimited("slow down")

    fake_llm.chat_json = limited
    with pytest.raises(LLMRateLimited):
        respond("Boston to Lisbon", today=TODAY)


def test_missing_key_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(lark.llm, "settings", lambda: {"LARK_LLM_API_KEY": "", "LARK_LLM_BASE_URL": "x", "LARK_LLM_MODEL": "y"})
    with pytest.raises(LLMNotConfigured):
        get_llm()


def test_parse_json_handles_fences():
    assert parse_json('Sure!\n```json\n{"a": 1}\n```') == {"a": 1}


def test_save_and_load_trip(tmp_path):
    plan = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)["plan"]
    path = tmp_path / "trips.csv"
    save_trip(plan, path)
    save_trip(plan, path)
    rows = load_trips(path)
    assert len(rows) == 2
    assert rows[0]["destination"] == "Lisbon, Portugal"
    assert rows[0]["budget"] == "3200"


# ---- retries and the fallback model (no network: _call is replaced) ----------

from lark.llm import LLM, LLMError as _LLMError, _Busy


def _llm_with(script, fallback="backup-model"):
    """An LLM whose _call follows `script`: a list of statuses (int) or reply strings."""
    llm = LLM("key", "https://example.invalid/v1", "main-model", fallback, sleep=lambda _s: None)
    calls = []

    def fake_call(model, _messages):
        calls.append(model)
        step = script.pop(0)
        if isinstance(step, int):
            raise _Busy(step)
        return step

    llm._call = fake_call
    return llm, calls


def test_busy_provider_is_retried_then_answers():
    llm, calls = _llm_with([503, 503, '{"ok": 1}'])
    assert llm.chat_json("plan", "sys", {}) == {"ok": 1}
    assert calls == ["main-model"] * 3


def test_fallback_model_is_used_when_main_stays_busy():
    llm, calls = _llm_with([503, 503, 503, 503, '{"ok": 2}'])
    assert llm.chat_json("plan", "sys", {}) == {"ok": 2}
    assert calls == ["main-model"] * 4 + ["backup-model"]


def test_unknown_main_model_skips_straight_to_fallback():
    llm, calls = _llm_with([404, '{"ok": 3}'])
    assert llm.chat_json("plan", "sys", {}) == {"ok": 3}
    assert calls == ["main-model", "backup-model"]


def test_everything_busy_gives_a_clear_error():
    llm, _calls = _llm_with([503] * 6)
    with pytest.raises(_LLMError, match="overloaded"):
        llm.chat_json("plan", "sys", {})


def test_rate_limit_everywhere_is_reported_as_rate_limit():
    llm, _calls = _llm_with([429] * 6)
    with pytest.raises(LLMRateLimited):
        llm.chat_json("plan", "sys", {})


def test_tradeoffs_sent_as_a_list_become_one_paragraph(fake_llm):
    respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)  # warm up the fake
    original = fake_llm.chat_json

    def listy(task, system, payload):
        answer = original(task, system, payload)
        if task == "plan":
            answer["tradeoffs"] = ["Cheaper flight.", "Nicer room."]
        return answer

    fake_llm.chat_json = listy
    plan = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)["plan"]
    assert plan["tradeoffs"].startswith("Cheaper flight. Nicer room.")
    assert "[" not in plan["tradeoffs"]


# ---- links to check every estimate ------------------------------------------

from urllib.parse import parse_qs, urlparse

from lark import links


def test_links_carry_the_trip_details():
    plan = respond("Two of us, Boston to Lisbon, 5 nights in June, $3200", today=TODAY)["plan"]
    stay = plan["stays"][plan["stay_index"]]

    flights = parse_qs(urlparse(links.google_flights(plan)).query)["q"][0]
    assert "BOS" in flights and "LIS" in flights and plan["depart"] in flights and "2 adults" in flights

    assert links.kayak(plan).endswith(f"/BOS-LIS/{plan['depart']}/{plan['ret']}/2adults")

    hotel = parse_qs(urlparse(links.booking(stay, plan)).query)
    assert hotel["ss"] == [f"{stay['name']}, Lisbon"]
    assert hotel["checkin"] == [plan["depart"]] and hotel["checkout"] == [plan["ret"]]

    spot = parse_qs(urlparse(links.place("Pastéis de Belém", "Belém", plan)).query)
    assert spot["query"] == ["Pastéis de Belém, Belém, Lisbon, Portugal"]
