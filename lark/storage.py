"""Saved trips live in one CSV file, one row per trip."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

SAVED_TRIPS = Path(__file__).resolve().parent.parent / "data" / "saved_trips.csv"

FIELDS = [
    "saved_at",
    "docket",
    "origin",
    "destination",
    "depart",
    "return",
    "nights",
    "travelers",
    "budget",
    "estimated_total",
    "fits_budget",
    "flight",
    "stay",
    "activities",
    "chosen_by",
    "tradeoffs",
]


def trip_row(plan: dict) -> dict:
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    return {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "docket": plan["docket"],
        "origin": plan["origin"],
        "destination": f"{plan['city']}, {plan['country']}",
        "depart": plan["depart"],
        "return": plan["ret"],
        "nights": plan["nights"],
        "travelers": plan["travelers"],
        "budget": plan["budget"],
        "estimated_total": plan["total"],
        "fits_budget": plan["fits"],
        "flight": f"{flight['carrier']} {flight['via']} (${flight['price']:,})",
        "stay": f"{stay['name']}, {stay['area']} (${stay['total']:,})",
        "activities": "; ".join(item["name"] for item in plan["activities"]),
        "chosen_by": plan.get("chosen_by", "rules"),
        "tradeoffs": plan.get("tradeoffs", ""),
    }


def save_trip(plan: dict, path: Path | None = None) -> dict:
    path = path or SAVED_TRIPS
    row = trip_row(plan)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row


def load_trips(path: Path | None = None) -> list[dict]:
    path = path or SAVED_TRIPS
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
