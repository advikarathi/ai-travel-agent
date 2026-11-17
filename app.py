"""Lark in Streamlit.

    streamlit run app.py
"""

from __future__ import annotations

from datetime import date, timedelta
import streamlit as st

from lark import export, extras, look
from lark.agent import respond
from lark.llm import LLMError, LLMRateLimited, is_configured, settings
from lark.parse import VIBE_WORDS
from lark.storage import SAVED_TRIPS, load_trips, save_trip

st.set_page_config(page_title="Lark", page_icon=":material/flight_takeoff:", layout="wide")

STARTERS = [
    "Two of us, Boston to Lisbon, 5 nights in June, $3200",
    "Where can we go from Boston for $2,500 in April? Two of us, 5 nights, food",
    "Solo from Chicago, a weekend in New Orleans, under $900",
    "From San Francisco to Tokyo in April, 6 nights, two people, food first, $4500",
]

PACES = ["Relaxed", "Balanced", "Packed"]
WALKING = ["Lots", "Some", "Minimal"]
DIETS = ["No restrictions", "Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-free"]

# ---- session state, all in one place ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # {"role", "content", "plan"?}
    st.session_state.lark_state = None  # the agent's trip state, fed back every turn
    st.session_state.suggestions = list(STARTERS)
    st.session_state.applied = {}  # sidebar values already pushed into lark_state
    st.session_state.retry = None  # message to resend after a rate limit
    st.session_state.sync = None  # plan values to show in the sidebar on the next run

# After a plan, the sidebar shows that trip's numbers, so it never looks empty.
if st.session_state.get("sync"):
    for key, value in st.session_state.sync.items():
        st.session_state[key] = value
    st.session_state.sync = None
    st.session_state.applied = {
        "budget": st.session_state.get("sb_budget"),
        "dates": tuple(st.session_state.get("sb_dates") or ()) or None,
        "travelers": st.session_state.get("sb_travelers"),
        "vibes": tuple(st.session_state.get("sb_vibes") or ()),
    }

st.markdown(look.STYLE, unsafe_allow_html=True)

# ---- sidebar: trip settings -------------------------------------------------
with st.sidebar:
    st.header("Trip settings")
    st.caption("Fill these in or just type in the chat. After a plan, they show that trip, and changing one replans it.")
    st.number_input(
        "Total budget (USD)", min_value=50, max_value=500_000, step=100, value=None, key="sb_budget", placeholder="e.g. 3200"
    )
    st.date_input(
        "Dates",
        # Empty until a plan fills it (a value here would clash with the plan's dates in session state).
        **({} if "sb_dates" in st.session_state else {"value": ()}),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=540),
        key="sb_dates",
        help="Pick a departure and a return date.",
    )
    st.number_input("Travelers", min_value=1, max_value=9, step=1, value=None, key="sb_travelers", placeholder="e.g. 2")
    st.pills("Vibe", sorted(VIBE_WORDS), selection_mode="multi", key="sb_vibes")
    with st.expander("About you", icon=":material/person:"):
        st.segmented_control("Pace", PACES, default="Balanced", key="sb_pace")
        st.segmented_control("Walking", WALKING, default="Some", key="sb_walking")
        st.selectbox("Food", DIETS, key="sb_diet")
        st.caption("Lark plans the days around these. Press Update plan after changing them.")
    replan = st.button("Update plan", icon=":material/refresh:", width="stretch", type="primary")
    if st.button("Start over", icon=":material/restart_alt:", width="stretch"):
        for key in ("messages", "lark_state", "suggestions", "applied", "retry", "sync"):
            st.session_state.pop(key, None)
        for key in ("sb_budget", "sb_dates", "sb_travelers", "sb_vibes", "sb_pace", "sb_walking", "sb_diet"):
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()
    st.caption(f"Model: `{settings()['LARK_LLM_MODEL']}`")


def sidebar_values() -> dict:
    dates = st.session_state.sb_dates
    return {
        "budget": st.session_state.sb_budget,
        "dates": tuple(dates) if isinstance(dates, (tuple, list)) and len(dates) == 2 else None,
        "travelers": st.session_state.sb_travelers,
        "vibes": tuple(st.session_state.sb_vibes or ()),
    }


def merge_sidebar(state: dict | None) -> dict:
    """Push sidebar values the user changed since last time into the trip state."""
    state = dict(state or {})
    values, applied = sidebar_values(), st.session_state.applied
    changed = {key: value for key, value in values.items() if value != applied.get(key)}
    if changed.get("budget"):
        state["budget"], state["per_person"] = int(changed["budget"]), False
    if changed.get("travelers"):
        state["travelers"] = int(changed["travelers"])
    if changed.get("dates"):
        start, end = changed["dates"]
        if end > start:
            state.update(
                depart=start.isoformat(),
                ret=end.isoformat(),
                nights=min(21, (end - start).days),
                month_hint=start.month,
                dates_assumed=False,
            )
    if "vibes" in changed:
        state["vibes"] = list(changed["vibes"])
    st.session_state.applied = values
    # The profile always rides along; only what differs from the defaults is sent.
    profile = {
        "pace": (st.session_state.get("sb_pace") or "Balanced").lower(),
        "walking": (st.session_state.get("sb_walking") or "Some").lower(),
        "diet": (st.session_state.get("sb_diet") or DIETS[0]).lower(),
    }
    state["profile"] = {k: v for k, v in profile.items() if v not in ("balanced", "some", "no restrictions")}
    return state


def last_plan() -> dict | None:
    for msg in reversed(st.session_state.messages):
        if msg.get("plan"):
            return msg["plan"]
    return None


def run_turn(message: str) -> None:
    state = merge_sidebar(st.session_state.lark_state)
    try:
        with st.spinner("Lark is checking flights, weather, stays and things to do against your budget..."):
            result = respond(message, state, current_plan=last_plan())
            if result["plan"]:
                plan = result["plan"]
                # Photos and map points from Wikipedia; cached, skipped if slow or offline.
                plan["extras"] = extras.enrich(plan, plan["lat"], plan["lon"])
    except LLMRateLimited as error:
        st.session_state.retry = message
        st.session_state.messages.append({"role": "assistant", "content": f":orange[{error}]", "error": True})
        return
    except LLMError as error:
        st.session_state.messages.append({"role": "assistant", "content": f":red[{error}]", "error": True})
        return
    st.session_state.retry = None
    st.session_state.lark_state = result["state"]
    st.session_state.suggestions = result["suggestions"] or st.session_state.suggestions
    if result["plan"]:
        st.session_state.suggestions = result["suggestions"] + ["What should I pack?", "Is this too rushed?"]
    plan = result["plan"]
    st.session_state.messages.append(
        {"role": "assistant", "content": result["reply"], "plan": plan, "notes": result.get("notes") or []}
    )
    if plan:
        sync = {"sb_budget": int(plan["budget"]), "sb_travelers": int(plan["travelers"])}
        start, end = date.fromisoformat(plan["depart"]), date.fromisoformat(plan["ret"])
        if date.today() <= start < end <= date.today() + timedelta(days=540):  # inside the picker's range
            sync["sb_dates"] = (start, end)
        st.session_state.sync = sync


# ---- the plan ---------------------------------------------------------------
def html(markup: str) -> None:
    # Markdown turns indented lines after a blank line into a code block, so flatten the HTML first.
    flat = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


def day_map(plan: dict, day: dict) -> None:
    places = (plan.get("extras") or {}).get("places") or {}
    points = [
        {"lat": places[item]["lat"], "lon": places[item]["lon"], "name": item}
        for item in day["items"]
        if item in places
    ]
    if points:
        st.map(points, latitude="lat", longitude="lon", size=60, color="#E0483E", zoom=11, height=260)
        if any(places[p["name"]].get("approximate") for p in points):
            st.caption("Some pins mark the neighbourhood, not the exact spot.")


def show_plan(plan: dict, index: int) -> None:
    flight = plan["flights"][plan["flight_index"]]
    stay = plan["stays"][plan["stay_index"]]
    found = plan.get("extras") or {}
    html(look.passport(plan))
    html(look.boarding_pass(plan, flight))
    html(look.luggage_tag(plan, flight, stay))
    note, photo = look.sticky_note(plan), look.polaroid(plan["city"], found.get("city_photo"))
    if note and photo:
        left, right = st.columns([3, 2])
        with left:
            html(note)
        with right:
            html(photo)
    else:
        html(note or photo)
    html(look.postcard(plan, stay))

    st.subheader("Your days")
    weather = plan.get("weather") or []
    if weather and weather[0].get("kind") == "last_year":
        st.caption("Too far out for a forecast, so each day shows last year's weather on the same date (Open-Meteo).")
    elif weather:
        st.caption("Forecast from Open-Meteo. Lark put the indoor plans on the wetter days.")
    tabs = st.tabs([day["label"] for day in plan["days"]])
    for offset, (tab, day) in enumerate(zip(tabs, plan["days"])):
        with tab:
            sky = weather[offset] if offset < len(weather) else None
            html(look.day_route(plan, day, sky, found.get("places")))
            day_map(plan, day)

    with st.expander("Other flights and stays Lark compared"):
        st.dataframe(
            [
                {"Flight": f"{f['carrier']} {f['code']}", "Stops": f["via"], "Time": f["duration"], "Price": look.money(f["price"])}
                for f in plan["flights"]
            ],
            hide_index=True,
        )
        st.dataframe(
            [
                {"Stay": s["name"], "Type": s["style"], "Area": s["area"], "Rating": s["rating"], "Total": look.money(s["total"])}
                for s in plan["stays"]
            ],
            hide_index=True,
        )

    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button("Save trip", key=f"save_{index}", icon=":material/bookmark_add:", type="primary"):
            save_trip(plan)  # the Saved trips list below is drawn after this, so it's current
            st.toast(f"Saved {plan['city']} to {SAVED_TRIPS.name}", icon=":material/check:")
        name = f"lark-{plan['city'].lower().replace(' ', '-')}-{plan['depart']}"
        st.download_button(
            "Download PDF", export.to_pdf(plan), f"{name}.pdf", "application/pdf",
            key=f"pdf_{index}", icon=":material/picture_as_pdf:", on_click="ignore",
        )
        st.download_button(
            "Add to calendar", export.to_ics(plan), f"{name}.ics", "text/calendar",
            key=f"ics_{index}", icon=":material/calendar_add_on:", on_click="ignore",
        )
        picked = "the LLM" if plan.get("chosen_by") == "llm" else "Lark's rules"
        sources = plan.get("sources") or {}
        if sources.get("flights") == "google":
            where = "The flight price is live from Google Flights; hotel and activity prices are estimates."
        else:
            where = "Prices are estimates; Google Flights didn't answer this time."
        html(f'<span class="lk-fine">Picked by {picked}. {where} The links open the booking sites.</span>')


# ---- main --------------------------------------------------------------------
html(look.hero())

if not is_configured():
    st.error(
        "Lark needs an LLM to plan trips. Copy `.env.example` to `.env` (or "
        "`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`), set `LARK_LLM_API_KEY`, "
        "and reload. Any OpenAI-compatible provider works; set `LARK_LLM_BASE_URL` and "
        "`LARK_LLM_MODEL` to match.",
        title="No LLM key found",
        icon=":material/key_off:",
    )
    st.stop()

for index, msg in enumerate(st.session_state.messages):
    avatar = ":material/flight_takeoff:" if msg["role"] == "assistant" else ":material/person:"
    with st.chat_message(msg["role"], avatar=avatar):
        content = msg["content"]
        plan = msg.get("plan")
        if plan and plan.get("tradeoffs"):
            content = content.replace("\n\n" + plan["tradeoffs"], "")  # shown in the plan instead
        st.markdown(content)
        for note in msg.get("notes") or []:
            st.caption(note)
        if plan:
            show_plan(plan, index)

pending = None
if st.session_state.retry and st.button("Try again", icon=":material/replay:"):
    pending = st.session_state.retry
if st.session_state.suggestions:
    label = "Try one of these" if not st.session_state.messages else "Change it"
    choice = st.pills(label, st.session_state.suggestions, key=f"suggest_{len(st.session_state.messages)}")
    if choice:
        pending = choice
if prompt := st.chat_input("e.g. Two of us, Boston to Lisbon, 5 nights in June, $3200", submit_mode="disable"):
    pending = prompt
if replan:
    pending = ""

st.divider()
trips = load_trips()
with st.expander(f"Saved trips ({len(trips)})", icon=":material/bookmarks:"):
    if trips:
        st.dataframe(trips, hide_index=True)
    else:
        st.caption("Nothing saved yet. Plan a trip and press Save trip.")

if pending is not None:
    if pending:
        st.session_state.messages.append({"role": "user", "content": pending})
    run_turn(pending)
    st.rerun()
