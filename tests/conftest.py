"""Tests never call a real model. FakeLLM stands in for lark.llm.LLM."""

from __future__ import annotations

import pytest

import lark.agent


class FakeLLM:
    """Extraction returns nothing new (so the rule parser's reading stands).

    Planning picks the cheapest flight, the cheapest non-hostel stay that fits, and
    the two cheapest activities, the way a sensible model would on a tight budget.
    Set `plan_override` / `extract_override` to script a specific answer.
    """

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.extract_override: dict | None = None
        self.plan_override: dict | None = None
        self.destination_override: dict | None = None

    def chat_json(self, task: str, system: str, payload: dict) -> dict:
        self.calls.append((task, payload))
        if task == "extract":
            return dict(self.extract_override or {})
        if task == "destination":
            if self.destination_override is not None:
                return dict(self.destination_override)
            fitting = [c for c in payload["candidates"] if c["fits"]] or payload["candidates"]
            best = max(fitting, key=lambda c: (c["season"] == "best", c["vibe_matches"], -c["estimated_total"]))
            return {"slug": best["slug"], "why": f"{best['city']} fits at ${best['estimated_total']:,}.", "runner_up": None}
        if task == "answer":
            return {"answer": f"About {payload['plan']['to']}: {payload['question']}"}
        if self.plan_override is not None:
            return dict(self.plan_override)
        options = payload["options"]
        trip = payload["trip"]
        flight = min(options["flights"], key=lambda item: item["price"])
        acts = sorted(options["activities"], key=lambda item: item["cost"])[:2]
        spare = trip["budget"] - flight["price"] - trip["meals"] - sum(a["cost"] for a in acts)
        stays = sorted(options["stays"], key=lambda item: item["total"])
        fitting = [s for s in stays if s["total"] <= spare and s["style"] != "Hostel"]
        stay = fitting[0] if fitting else stays[0]
        dates = payload["dates"]
        days = [{"title": "Day", "activity_ids": [], "note": "Wander."} for _ in dates]
        for index, act in enumerate(acts):
            days[index % len(days)]["activity_ids"].append(act["id"])
        return {
            "flight_id": flight["id"],
            "stay_id": stay["id"],
            "activity_ids": [a["id"] for a in acts],
            "days": days,
            "tradeoffs": "Took the cheapest seat so the room could be nicer.",
        }


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(lark.agent, "get_llm", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def no_live_prices(monkeypatch):
    """Tests never call Google Flights; the planner falls back to estimates."""
    import lark.live

    monkeypatch.setattr(lark.live, "_fetch", lambda *args: None)


@pytest.fixture(autouse=True)
def no_free_extras(monkeypatch):
    """Tests never call Open-Meteo or Wikipedia."""
    import lark.extras

    monkeypatch.setattr(lark.extras, "_get_json", lambda *args, **kwargs: None)
