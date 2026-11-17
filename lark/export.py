"""Take a plan with you: a calendar file (.ics) and a one-page-per-trip PDF."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

# The PDF's built-in fonts only cover Latin-1, so swap the few characters that aren't in it.
_PLAIN = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "→": "to", "★": " stars", "…": "...", "·": "-", "°": " deg"}


def _plain(text: object) -> str:
    text = str(text or "")
    for fancy, simple in _PLAIN.items():
        text = text.replace(fancy, simple)
    return text.encode("latin-1", "replace").decode("latin-1")


def _money(value: int) -> str:
    return f"${value:,}"


# ---- calendar --------------------------------------------------------------------
def _ics_text(text: object) -> str:
    return str(text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def to_ics(plan: dict) -> bytes:
    """All-day events: one per day of the trip, plus the flight out and back."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    start = date.fromisoformat(plan["depart"])
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Lark//Trip planner//EN", "CALSCALE:GREGORIAN"]

    def event(uid: str, day: date, summary: str, description: str) -> None:
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}@lark",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(day + timedelta(days=1)).strftime('%Y%m%d')}",
                f"SUMMARY:{_ics_text(summary)}",
                f"DESCRIPTION:{_ics_text(description)}",
                f"LOCATION:{_ics_text(plan['city'] + ', ' + plan['country'])}",
                "END:VEVENT",
            ]
        )

    trip_id = f"{plan['origin_code']}-{plan['dest_code']}-{plan['depart']}"
    event(
        f"{trip_id}-out", start, f"Fly {plan['origin_code']} to {plan['dest_code']} ({flight['carrier']})",
        f"Leaves {flight['depart_time']}, arrives {flight['arrive_time']}. {flight['via']}. Stay: {stay['name']}, {stay['area']}.",
    )
    for offset, day in enumerate(plan["days"]):
        event(f"{trip_id}-day{offset}", start + timedelta(days=offset), f"{plan['city']}: {day['title']}", "\n".join(day["items"]))
    event(f"{trip_id}-back", date.fromisoformat(plan["ret"]), f"Fly home from {plan['city']}", f"{flight['carrier']}, {flight['via']}.")
    lines.append("END:VCALENDAR")
    # Calendar lines must end in CRLF.
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


# ---- PDF -------------------------------------------------------------------------
def to_pdf(plan: dict) -> bytes:
    from fpdf import FPDF

    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    weather = {day["date"]: day for day in plan.get("weather") or []}
    navy, blue, red, muted = (19, 41, 75), (36, 87, 184), (224, 72, 62), (91, 107, 130)

    pdf = FPDF(format="letter")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    # Airmail stripe across the top.
    for index in range(0, 30):
        pdf.set_fill_color(*(red if index % 2 == 0 else blue))
        pdf.rect(index * 7.2, 0, 7.2, 3, style="F")

    def text(size, value, color=navy, style="", gap=1.5, width=0):
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(width, size * 0.48, _plain(value), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(gap)

    pdf.set_y(14)
    text(26, f"{plan['origin_code']} to {plan['dest_code']}: {plan['city']}", style="B", gap=1)
    people = "1 traveler" if plan["travelers"] == 1 else f"{plan['travelers']} travelers"
    text(11, f"{plan['depart_label']} to {plan['ret_label']}  |  {plan['nights']} nights  |  {people}", color=muted, gap=5)

    left = "Left over" if plan["fits"] else "Over budget by"
    text(13, f"Estimated total {_money(plan['total'])} of a {_money(plan['budget'])} budget. {left}: {_money(abs(plan['pocket']))}.", style="B", gap=4)

    fare = "Google Flights fare" if (plan.get("sources") or {}).get("flights") == "google" else "Estimated fare"
    text(12, "Flight", color=blue, style="B", gap=0.5)
    text(11, f"{flight['carrier']}, {flight['via']}, {flight['duration']}. Leaves {flight['depart_time']}, arrives {flight['arrive_time']}.", gap=0.5)
    text(11, f"{fare}: {_money(flight['price'])} round trip for {plan['travelers']} ({_money(flight['per_person'])} each).", color=muted, gap=4)

    text(12, "Stay", color=blue, style="B", gap=0.5)
    text(11, f"{stay['name']}, {stay['style']} in {stay['area']}, rated {stay['rating']}.", gap=0.5)
    text(11, f"{stay['nights']} nights at {_money(stay['nightly'])} a night: {_money(stay['total'])} (estimate).", color=muted, gap=4)

    if plan.get("tradeoffs"):
        text(12, "Why this plan", color=blue, style="B", gap=0.5)
        text(11, plan["tradeoffs"], style="I", gap=4)

    text(12, "Day by day", color=blue, style="B", gap=1)
    start = date.fromisoformat(plan["depart"])
    for offset, day in enumerate(plan["days"]):
        when = (start + timedelta(days=offset)).isoformat()
        sky = weather.get(when)
        sky_text = f"   {sky['summary']}, {sky['high']}/{sky['low']} F" if sky else ""
        text(11.5, f"{day['label']}: {day['title']}{sky_text}", style="B", gap=0.3)
        for item in day["items"]:
            text(10.5, f"-  {item}", gap=0.2)
        pdf.ln(2)

    pdf.ln(2)
    text(9, "Hotel, meal and activity prices are Lark's estimates. Check live prices before booking. Planned with Lark.", color=muted)
    return bytes(pdf.output())
