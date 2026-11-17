"""Lark's evaluation set: 10 realistic requests, each checked for budget honesty.

    python evaluate.py              # real LLM + live Google Flights (uses your .env)
    python evaluate.py --estimates  # real LLM, Lark's estimated fares only (faster)

For every request it records whether a plan came back, whether the LLM's own
pick was used (or Lark fell back to rules), whether the plan fits the budget,
whether the total adds up from its parts, and how long it took. Results print
as a table and are saved to data/eval_results.csv.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

CASES = [
    "Two of us, Boston to Lisbon, 5 nights in June, $3200",
    "Solo from Chicago, a weekend in New Orleans, under $900",
    "From San Francisco to Tokyo in April, 6 nights, two people, food first, $4500",
    "Family of four from New York to Barcelona, a week in July, $9000",
    "Solo from Boston to Paris, 4 nights in March, $1800, museums",
    "Two of us from Los Angeles to Mexico City, 5 nights in May, $2200, food and nightlife",
    "From Chicago to Reykjavik, 4 nights in September, two people, $3500, adventure",
    "Three friends from Boston to London, 5 nights in October, $5000 total",
    "Where can we go from New York for $2,500 in April? Two of us, 5 nights",
    "Solo from Boston to Marrakech, a week in November, $1500, quiet",
]


def adds_up(plan: dict) -> bool:
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    parts = flight["price"] + stay["total"] + plan["meals"] + sum(a["cost"] for a in plan["activities"])
    return parts == plan["total"] and plan["pocket"] == plan["budget"] - plan["total"]


def check(message: str, respond_fn) -> dict:
    started = time.time()
    row = {"request": message, "city": "", "budget": "", "total": "", "fits": "", "adds_up": "", "picked_by": "", "fares": "", "seconds": "", "error": ""}
    try:
        result = respond_fn(message)
    except Exception as error:  # an LLM error is a result too
        row.update(error=str(error)[:120], seconds=round(time.time() - started, 1))
        return row
    plan = result.get("plan")
    row["seconds"] = round(time.time() - started, 1)
    if not plan:
        row["error"] = "No plan: " + result.get("reply", "")[:100]
        return row
    row.update(
        city=plan["city"],
        budget=plan["budget"],
        total=plan["total"],
        fits=plan["fits"],
        adds_up=adds_up(plan),
        picked_by=plan.get("chosen_by", "rules"),
        fares=(plan.get("sources") or {}).get("flights", "desk"),
    )
    return row


def summary(rows: list[dict]) -> str:
    plans = [r for r in rows if r["city"]]
    count = len(rows)
    lines = [
        f"Plans returned:       {len(plans)}/{count}",
        f"Under budget:         {sum(1 for r in plans if r['fits'] is True)}/{len(plans)}",
        f"Totals add up:        {sum(1 for r in plans if r['adds_up'] is True)}/{len(plans)}",
        f"LLM's pick used:      {sum(1 for r in plans if r['picked_by'] == 'llm')}/{len(plans)}",
        f"Live Google fares:    {sum(1 for r in plans if r['fares'] == 'google')}/{len(plans)}",
    ]
    if plans:
        times = sorted(float(r["seconds"]) for r in plans)
        lines.append(f"Seconds per plan:     median {times[len(times) // 2]}, slowest {times[-1]}")
    return "\n".join(lines)


def main() -> None:
    from lark.agent import respond

    if "--estimates" in sys.argv:
        import lark.live

        lark.live._fetch = lambda *args: None
    rows = []
    for message in CASES:
        row = check(message, respond)
        rows.append(row)
        status = row["error"] or f"{row['city']}: ${row['total']:,} of ${row['budget']:,}, fits={row['fits']}, by {row['picked_by']}, {row['seconds']}s"
        print(f"- {message[:60]:<60}  {status}")
    print()
    print(summary(rows))
    out = Path(__file__).resolve().parent / "data" / "eval_results.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
