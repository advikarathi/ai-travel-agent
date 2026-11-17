"""The evaluation set, run against the fake model: every plan must be honest about money."""

from __future__ import annotations

from datetime import date

import pytest

from evaluate import CASES, check, summary
from lark.agent import respond

TODAY = date(2026, 11, 9)


@pytest.mark.parametrize("message", CASES)
def test_every_case_plans_and_adds_up(message):
    row = check(message, lambda text: respond(text, today=TODAY))
    assert row["error"] == "", row["error"]
    assert row["adds_up"] is True
    assert row["picked_by"] == "llm"


def test_fitting_cases_stay_under_budget():
    rows = [check(message, lambda text: respond(text, today=TODAY)) for message in CASES]
    # Every case but the deliberately tight Marrakech one has room in its budget.
    assert all(row["fits"] for row in rows[:-1])
    assert "Plans returned:       10/10" in summary(rows)
