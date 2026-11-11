"""How a Lark plan looks: travel paper, not dashboard cards.

The flight is a boarding pass, the budget a luggage tag, the stay a postcard,
the model's reasoning a sticky note, and each day a dotted route with pins.
Every function returns an HTML string for st.markdown(..., unsafe_allow_html=True).
All text from the plan or the model is escaped.
"""

from __future__ import annotations

from html import escape

from lark import links

# Airmail paper: sky page, white tickets, airmail blue and red, a sunny yellow.
SKY = "#E8F1F8"
INK = "#13294B"
BLUE = "#2457B8"
RED = "#E0483E"
SUN = "#FFC845"
MUTED = "#5B6B82"

# Budget slices: color, label.
SLICES = [("#2457B8", "Flights"), ("#E0483E", "Stay"), ("#13294B", "Meals"), ("#2E8B57", "Things to do")]

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,400..800&family=Caveat:wght@500;700&display=swap');
html, body, .stApp {{ font-family: 'Bricolage Grotesque', system-ui, sans-serif; color: {INK}; }}
h1, h2, h3 {{ font-family: 'Bricolage Grotesque', system-ui, sans-serif !important; }}
[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid #D3E1EE; }}
.block-container {{ padding-top: 1.6rem; max-width: 1120px; }}
.lk a {{ color: {BLUE}; }}

/* hero */
.lk-hero {{ display: grid; grid-template-columns: 1.1fr 1fr; gap: 12px; align-items: center; margin-bottom: 8px; }}
.lk-hero h1 {{ font-size: 3.4rem; line-height: 1; font-weight: 800; font-stretch: 80%; margin: 0 0 12px; color: {INK}; letter-spacing: -0.02em; }}
.lk-hero p {{ font-size: 1.08rem; line-height: 1.5; color: {MUTED}; max-width: 34em; margin: 0; }}
.lk-hero svg {{ width: 100%; height: auto; }}
@media (max-width: 760px) {{ .lk-hero {{ grid-template-columns: 1fr; }} .lk-hero h1 {{ font-size: 2.5rem; }} }}
@media (prefers-reduced-motion: reduce) {{ .lk-fly {{ display: none; }} }}

/* airmail stripe */
.lk-stripe {{ height: 10px; background: repeating-linear-gradient(-45deg, {RED} 0 14px, #FFFFFF 14px 22px, {BLUE} 22px 36px, #FFFFFF 36px 44px); }}

/* boarding pass */
.lk-pass {{ background: #FFFFFF; border-radius: 18px; overflow: hidden; box-shadow: 0 10px 30px rgba(19,41,75,.12); margin: 8px 0 18px; }}
.lk-pass-body {{ display: grid; grid-template-columns: 1fr 230px; }}
.lk-pass-main {{ padding: 22px 28px 20px; }}
.lk-pass-top {{ display: flex; justify-content: space-between; color: {MUTED}; font-size: .95rem; }}
.lk-pass-top b {{ color: {INK}; font-weight: 700; }}
.lk-route {{ display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 14px; margin: 10px 0 6px; }}
.lk-iata {{ font-size: 4.2rem; line-height: .95; font-weight: 800; font-stretch: 75%; color: {INK}; letter-spacing: -0.01em; }}
.lk-place {{ color: {MUTED}; font-size: .95rem; }}
.lk-time {{ font-weight: 700; font-size: 1.05rem; margin-top: 2px; }}
.lk-end {{ text-align: right; }}
.lk-route svg {{ width: 100%; height: 64px; }}
.lk-fields {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; border-top: 1px dashed #C9D9EA; padding-top: 12px; margin-top: 6px; }}
.lk-fields span {{ display: block; color: {MUTED}; font-size: .82rem; }}
.lk-fields b {{ font-size: 1.02rem; }}
.lk-stub {{ position: relative; padding: 22px 22px 18px; border-left: 2px dashed #C9D9EA; background: #F6FAFD; display: flex; flex-direction: column; gap: 6px; }}
.lk-stub::before, .lk-stub::after {{ content: ""; position: absolute; left: -13px; width: 24px; height: 24px; border-radius: 50%; background: {SKY}; }}
.lk-stub::before {{ top: -12px; }} .lk-stub::after {{ bottom: -12px; }}
.lk-stub span {{ color: {MUTED}; font-size: .85rem; }}
.lk-fare {{ font-size: 2.1rem; font-weight: 800; line-height: 1; }}
.lk-barcode {{ height: 38px; margin: 6px 0 4px; background: repeating-linear-gradient(90deg, {INK} 0 2px, transparent 2px 4px, {INK} 4px 7px, transparent 7px 9px, {INK} 9px 10px, transparent 10px 13px); opacity: .85; }}
.lk-btn {{ display: inline-block; padding: 7px 12px; border-radius: 999px; border: 1.5px solid {BLUE}; color: {BLUE} !important; font-weight: 600; font-size: .9rem; text-decoration: none !important; margin: 4px 6px 0 0; background: #FFFFFF; }}
.lk-btn:hover {{ background: {BLUE}; color: #FFFFFF !important; }}
.lk-btn:focus-visible {{ outline: 3px solid {SUN}; outline-offset: 2px; }}
@media (max-width: 760px) {{ .lk-pass-body {{ grid-template-columns: 1fr; }} .lk-stub {{ border-left: none; border-top: 2px dashed #C9D9EA; }}
  .lk-stub::before, .lk-stub::after {{ display: none; }} .lk-iata {{ font-size: 3rem; }} .lk-fields {{ grid-template-columns: repeat(2, 1fr); }} }}

/* luggage tag */
.lk-tag {{ position: relative; background: {SUN}; color: {INK}; padding: 18px 26px 18px 70px; margin: 0 0 18px;
  clip-path: polygon(34px 0, 100% 0, 100% 100%, 34px 100%, 0 calc(100% - 34px), 0 34px); border-radius: 0 16px 16px 0; }}
.lk-tag::before {{ content: ""; position: absolute; left: 26px; top: 50%; width: 22px; height: 22px; margin-top: -11px; border-radius: 50%; background: {SKY}; box-shadow: inset 0 0 0 4px #E6B02F; }}
.lk-tag-row {{ display: flex; gap: 36px; flex-wrap: wrap; align-items: baseline; }}
.lk-tag-row span {{ display: block; font-size: .85rem; }}
.lk-tag-row b {{ font-size: 1.9rem; font-weight: 800; line-height: 1.1; }}
.lk-tag-row .lk-over b {{ color: #A3241C; }}
.lk-bar {{ display: flex; height: 14px; border-radius: 99px; overflow: hidden; background: rgba(255,255,255,.55); margin-top: 12px; }}
.lk-legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 8px; font-size: .9rem; }}
.lk-dot {{ display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; border: 1.5px solid #FFFFFF; }}

/* sticky note */
.lk-note {{ position: relative; background: #FFF4B8; padding: 22px 22px 16px; transform: rotate(-1.2deg); box-shadow: 0 8px 18px rgba(19,41,75,.12); margin: 6px 6px 22px; max-width: 640px; }}
.lk-note::before {{ content: ""; position: absolute; top: -10px; left: 50%; width: 90px; height: 22px; margin-left: -45px; background: rgba(255,255,255,.65); transform: rotate(2deg); }}
.lk-note p {{ font-family: 'Caveat', cursive; font-size: 1.45rem; line-height: 1.3; margin: 0; color: #2B2B2B; }}
.lk-note small {{ display: block; font-family: 'Caveat', cursive; font-size: 1.15rem; color: {MUTED}; margin-top: 6px; }}

/* postcard */
.lk-card {{ display: grid; grid-template-columns: 1fr 190px; background: #FFFFFF; border-radius: 6px; box-shadow: 0 10px 30px rgba(19,41,75,.12); margin: 0 0 22px; overflow: hidden; }}
.lk-card-msg {{ padding: 22px 26px; border-right: 1.5px solid #D3E1EE; }}
.lk-card-msg h3 {{ font-size: 1.6rem; font-weight: 800; margin: 2px 0 2px; color: {INK}; }}
.lk-card-msg .lk-kind {{ color: {MUTED}; }}
.lk-card-msg p {{ font-family: 'Caveat', cursive; font-size: 1.35rem; line-height: 1.25; margin: 10px 0 8px; color: #2B2B2B; }}
.lk-card-side {{ padding: 18px; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; background: #FFFFFF; }}
.lk-stamp {{ width: 92px; padding: 8px; background: {BLUE}; color: #FFFFFF; text-align: center; outline: 3px dotted #FFFFFF; outline-offset: -6px; border: 6px solid #FFFFFF; box-shadow: 0 0 0 1px #D3E1EE; }}
.lk-stamp b {{ display: block; font-size: 1.6rem; font-weight: 800; line-height: 1; }}
.lk-stamp span {{ font-size: .75rem; }}
.lk-lines {{ width: 100%; font-size: .95rem; }}
.lk-lines div {{ border-bottom: 1.5px solid #D3E1EE; padding: 5px 0; }}
.lk-lines b {{ float: right; }}
@media (max-width: 760px) {{ .lk-card {{ grid-template-columns: 1fr; }} .lk-card-msg {{ border-right: none; border-bottom: 1.5px solid #D3E1EE; }} }}

/* the days */
.lk-day-title {{ font-size: 1.3rem; font-weight: 800; margin: 6px 0 10px; }}
.lk-route-list {{ position: relative; margin-left: 10px; padding-left: 26px; border-left: 3px dotted {BLUE}; }}
.lk-stop {{ position: relative; padding: 2px 0 18px; }}
.lk-stop::before {{ content: ""; position: absolute; left: -36px; top: 4px; width: 16px; height: 16px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); background: {RED}; box-shadow: 0 0 0 3px {SKY}; }}
.lk-stop.lk-open::before {{ background: #FFFFFF; border: 2px solid {BLUE}; width: 12px; height: 12px; left: -34px; }}
.lk-stop-head {{ display: flex; justify-content: space-between; gap: 12px; }}
.lk-stop-head b {{ font-size: 1.08rem; }}
.lk-cost {{ font-weight: 700; white-space: nowrap; }}
.lk-stop .lk-area {{ color: {MUTED}; }}
.lk-stop p {{ margin: 2px 0 4px; color: {MUTED}; }}
.lk-fine {{ color: {MUTED}; font-size: .88rem; }}
</style>
"""


def money(value: int) -> str:
    return f"${value:,}"


def hero() -> str:
    """Headline plus a small sky: two pins and a plane flying the dotted arc between them."""
    return f"""
<div class="lk lk-hero">
  <div>
    <h1>Where to next?</h1>
    <p>Tell Lark where you want to go, when, who is coming and what you can spend.
    It picks the flight, the place to stay and what to do each day, then links you to live prices.</p>
  </div>
  <svg viewBox="0 0 440 210" role="img" aria-label="A plane flying a dotted route between two map pins">
    <circle cx="372" cy="52" r="30" fill="{SUN}"/>
    <g fill="#FFFFFF"><ellipse cx="96" cy="58" rx="42" ry="15"/><ellipse cx="124" cy="48" rx="26" ry="15"/>
       <ellipse cx="300" cy="120" rx="36" ry="12"/><ellipse cx="322" cy="112" rx="22" ry="12"/></g>
    <path id="lk-arc" d="M60 178 C 140 40, 300 30, 380 160" fill="none" stroke="{BLUE}" stroke-width="3"
          stroke-dasharray="2 9" stroke-linecap="round"/>
    <g fill="{RED}"><path d="M60 182 c-12-14-18-22-18-31a18 18 0 0 1 36 0c0 9-6 17-18 31z"/>
       <path d="M380 164 c-12-14-18-22-18-31a18 18 0 0 1 36 0c0 9-6 17-18 31z"/></g>
    <g fill="#FFFFFF"><circle cx="60" cy="151" r="6"/><circle cx="380" cy="133" r="6"/></g>
    <g class="lk-fly">
      <path d="M-14 0 L14 0 M2 0 L-6 -11 M2 0 L-6 11 M-12 0 L-16 -5 M-12 0 L-16 5" stroke="{INK}" stroke-width="4"
            stroke-linecap="round" fill="none"/>
      <animateMotion dur="6s" repeatCount="indefinite" rotate="auto" keyPoints="0;1" keyTimes="0;1" calcMode="spline"
                     keySplines=".45 0 .55 1"><mpath href="#lk-arc"/></animateMotion>
    </g>
  </svg>
</div>"""


def boarding_pass(plan: dict, flight: dict) -> str:
    stops = "Nonstop" if not flight.get("stops") else flight["via"]
    people = "1 traveler" if plan["travelers"] == 1 else f"{plan['travelers']} travelers"
    live = (plan.get("sources") or {}).get("flights") == "google"
    fare_label = f"Google Flights fare, round trip for {plan['travelers']}" if live else f"Estimated fare for {plan['travelers']}"
    code_line = f"Flight {escape(flight['code'])}" if flight.get("code") else ("Live from Google Flights" if live else "Estimate")
    return f"""
<div class="lk lk-pass">
  <div class="lk-stripe"></div>
  <div class="lk-pass-body">
    <div class="lk-pass-main">
      <div class="lk-pass-top"><b>{escape(flight['carrier'])}</b><span>{code_line}</span></div>
      <div class="lk-route">
        <div><div class="lk-iata">{escape(plan['origin_code'])}</div><div class="lk-place">{escape(plan['origin'])}</div>
             <div class="lk-time">{escape(flight['depart_time'])}</div></div>
        <svg viewBox="0 0 300 64" preserveAspectRatio="none" aria-hidden="true">
          <path d="M6 54 Q150 -6 294 54" fill="none" stroke="{BLUE}" stroke-width="2.5" stroke-dasharray="2 8" stroke-linecap="round"/>
          <g transform="translate(150 24)"><path d="M-12 0 L12 0 M2 0 L-5 -9 M2 0 L-5 9 M-10 0 L-13 -4 M-10 0 L-13 4"
             stroke="{RED}" stroke-width="3.5" stroke-linecap="round" fill="none"/></g>
        </svg>
        <div class="lk-end"><div class="lk-iata">{escape(plan['dest_code'])}</div><div class="lk-place">{escape(plan['city'])}</div>
             <div class="lk-time">{escape(flight['arrive_time'])}</div></div>
      </div>
      <div class="lk-fields">
        <div><span>Leave</span><b>{escape(plan['depart_label'])}</b></div>
        <div><span>Return</span><b>{escape(plan['ret_label'])}</b></div>
        <div><span>Who</span><b>{people}</b></div>
        <div><span>{escape(stops)}</span><b>{escape(flight['duration'])}</b></div>
      </div>
    </div>
    <div class="lk-stub">
      <span>{fare_label}</span>
      <div class="lk-fare">{money(flight['price'])}</div>
      <span>{money(flight['per_person'])} each</span>
      <div class="lk-barcode" aria-hidden="true"></div>
      <div>
        <a class="lk-btn" href="{escape(links.google_flights(plan))}" target="_blank" rel="noopener">Google Flights</a>
        <a class="lk-btn" href="{escape(links.kayak(plan))}" target="_blank" rel="noopener">Kayak</a>
      </div>
    </div>
  </div>
</div>"""


def luggage_tag(plan: dict, flight: dict, stay: dict) -> str:
    things = sum(a["cost"] for a in plan["activities"])
    parts = [flight["price"], stay["total"], plan["meals"], things]
    scale = max(plan["budget"], plan["total"]) or 1
    bar = "".join(
        f'<div style="width:{100 * amount / scale:.2f}%;background:{color}"></div>'
        for (color, _name), amount in zip(SLICES, parts)
        if amount
    )
    legend = "".join(
        f'<span><i class="lk-dot" style="background:{color}"></i>{name} {money(amount)}</span>'
        for (color, name), amount in zip(SLICES, parts)
    )
    if plan["fits"]:
        left = f'<div><span>Left over</span><b>{money(plan["pocket"])}</b></div>'
    else:
        left = f'<div class="lk-over"><span>Over budget by</span><b>{money(-plan["pocket"])}</b></div>'
    return f"""
<div class="lk lk-tag">
  <div class="lk-tag-row">
    <div><span>Whole trip, estimated</span><b>{money(plan['total'])}</b></div>
    <div><span>Your budget</span><b>{money(plan['budget'])}</b></div>
    {left}
  </div>
  <div class="lk-bar" role="img" aria-label="Where the money goes">{bar}</div>
  <div class="lk-legend">{legend}</div>
</div>"""


def sticky_note(plan: dict) -> str:
    if not plan.get("tradeoffs"):
        return ""
    signed = "Lark" if plan.get("chosen_by") == "llm" else "Lark's rules"
    return f"""
<div class="lk lk-note"><p>{escape(plan['tradeoffs'])}</p><small>— {signed}</small></div>"""


def postcard(plan: dict, stay: dict) -> str:
    note = f"<p>{escape(stay['note'])}</p>" if stay.get("note") else ""
    where = escape(plan["city"]) if stay["area"] == plan["city"] else f"{escape(stay['area'])}, {escape(plan['city'])}"
    live = (plan.get("sources") or {}).get("stays") == "google"
    price_from = "Price from Google Hotels" if live else "Lark’s estimate. Booking.com shows the live rate."
    own = (
        f'<a class="lk-btn" href="{escape(stay["link"])}" target="_blank" rel="noopener">Hotel’s own site</a>'
        if stay.get("link", "").startswith("http")
        else ""
    )
    return f"""
<div class="lk lk-card">
  <div class="lk-card-msg">
    <div class="lk-kind">{escape(stay['style'])} in {where}</div>
    <h3>{escape(stay['name'])}</h3>
    {note}
    <a class="lk-btn" href="{escape(links.booking(stay, plan))}" target="_blank" rel="noopener">See prices on Booking.com</a>
    <a class="lk-btn" href="{escape(links.place(stay['name'], stay['area'], plan))}" target="_blank" rel="noopener">Open in Maps</a>
    {own}
  </div>
  <div class="lk-card-side">
    <div class="lk-stamp"><b>{stay['rating']}★</b><span>guest rating</span></div>
    <div class="lk-lines">
      <div>Nights <b>{stay['nights']}</b></div>
      <div>A night <b>{money(stay['nightly'])}</b></div>
      <div>Total <b>{money(stay['total'])}</b></div>
    </div>
    <span class="lk-fine">{price_from}</span>
  </div>
</div>"""


def day_route(plan: dict, day: dict) -> str:
    by_name = {a["name"]: a for a in plan["activities"]}
    stops = []
    for item in day["items"]:
        activity = by_name.get(item)
        if activity:
            cost = "Free" if not activity["cost"] else money(activity["cost"])
            url = escape(links.place(activity["name"], activity["area"], plan))
            stops.append(
                f'<div class="lk-stop"><div class="lk-stop-head"><div><b>{escape(activity["name"])}</b> '
                f'<span class="lk-area">in {escape(activity["area"])}</span></div><span class="lk-cost">{cost}</span></div>'
                f'<p>{escape(activity["note"])}</p>'
                f'<a href="{url}" target="_blank" rel="noopener">Open in Maps</a></div>'
            )
        else:
            stops.append(f'<div class="lk-stop lk-open"><p>{escape(item)}</p></div>')
    return (
        f'<div class="lk"><div class="lk-day-title">{escape(day["title"])}</div>'
        f'<div class="lk-route-list">{"".join(stops)}</div></div>'
    )
