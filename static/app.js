const INTRO =
  "I'm Lark. Wing looks at flights, Hearth finds a room, Wander fills the days. I don't send them out until I know what the trip is allowed to cost.";

const STARTER_CHIPS = [
  "Two of us, Boston to Lisbon, 5 nights in June, $3200",
  "Solo from Chicago, a weekend in New Orleans, under $900",
  "From San Francisco to Tokyo in April, 6 nights, two people, food first, $4500",
];

const thread = document.querySelector("#thread");
const chips = document.querySelector("#chips");
const trip = document.querySelector("#trip");
const form = document.querySelector("#composer");
const say = document.querySelector("#say");
const sendButton = document.querySelector("#send");
const stampCount = document.querySelector("#stamp-count");
const passport = document.querySelector("#passport");
const passportList = document.querySelector("#passport-list");

let state = null;
let plan = null;
let messages = [{ role: "lark", text: INTRO }];
let suggestions = STARTER_CHIPS.slice();
let renderToken = 0;
let busy = false;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function money(amount) {
  const rounded = Math.round(Number(amount) || 0);
  const sign = rounded < 0 ? "−" : "";
  return `${sign}$${Math.abs(rounded).toLocaleString("en-US")}`;
}

function wait(ms) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return Promise.resolve();
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function posterHtml() {
  return document.querySelector(".poster")
    ? document.querySelector("#trip").innerHTML
    : "";
}

const POSTER = document.querySelector("#trip").innerHTML;

function renderThread() {
  thread.innerHTML = messages
    .map(
      (message) => `
      <article class="slip ${message.role}">
        <p class="who">${message.role === "user" ? "You" : "Lark"}</p>
        <p>${esc(message.text)}</p>
      </article>`
    )
    .join("");
  thread.scrollTop = thread.scrollHeight;
}

function renderChips() {
  chips.innerHTML = suggestions
    .map((chip) => `<button type="button" data-chip="${esc(chip)}">${esc(chip)}</button>`)
    .join("");
}

function totals() {
  const flight = plan.flights[plan.flight_index];
  const stay = plan.stays[plan.stay_index];
  const play = plan.activities.reduce((sum, item) => sum + item.cost, 0);
  const wander = play + plan.meals;
  const total = flight.price + stay.total + wander;
  return {
    flight,
    stay,
    play,
    wander,
    total,
    pocket: plan.budget - total,
    fits: total <= plan.budget,
  };
}

function scoutBlurb() {
  const now = totals();
  const wing = now.flight.stops
    ? `One stop on ${now.flight.carrier}, ${money(now.flight.price)} for the party.`
    : `Nonstop on ${now.flight.carrier}, ${money(now.flight.price)} for the party.`;
  const hearth = `${now.stay.name} in ${now.stay.area}. ${money(now.stay.total)} for ${now.stay.nights} nights.`;
  const wander = `${plan.activities.length} plans and ${money(plan.meals)} for the table, about ${money(plan.meal_rate)} a day each.`;
  return { wing, hearth, wander, ...now };
}

function renderPlan() {
  const snap = scoutBlurb();
  const source = "Desk estimates, not a booking. Sample flight numbers.";
  const dateNote = plan.dates_assumed ? ` I chose ${esc(plan.depart_label)}.` : "";
  trip.innerHTML = `
    <article class="docket">
      <div class="band">
        <p class="docket-no">${esc(plan.docket)} · ${esc(plan.origin_code)}–${esc(plan.dest_code)}</p>
        <div class="rubber ${snap.fits ? "" : "over"}">${snap.fits ? "Fits" : "Over"}</div>
      </div>
      <h2 class="city">${esc(plan.city)}</h2>
      <p class="meta">${esc(plan.depart_label)} – ${esc(plan.ret_label)} · ${plan.nights} nights · ${plan.travelers} ${plan.travelers === 1 ? "traveler" : "travelers"} · budget ${money(plan.budget)}</p>
      <p class="read">${esc(plan.read)}</p>
      <p class="source-note">${esc(source)}${dateNote}</p>
      <div class="envelopes">
        <div class="env wing"><span>Wing</span><strong>${money(snap.flight.price)}</strong></div>
        <div class="env hearth"><span>Hearth</span><strong>${money(snap.stay.total)}</strong></div>
        <div class="env wander"><span>Wander</span><strong>${money(snap.wander)}</strong></div>
        <div class="env pocket ${snap.fits ? "" : "short"}"><span>${snap.fits ? "Pocket" : "Short"}</span><strong>${money(snap.fits ? snap.pocket : -snap.pocket)}</strong></div>
      </div>

      <h3 class="section-label">Wing <span>the flight</span></h3>
      <div class="pass">
        <div class="pass-main">
          <div class="route">
            <div>
              <div class="code">${esc(plan.origin_code)}</div>
              <p class="when">${esc(snap.flight.depart_time)}</p>
              <p class="where">${esc(plan.origin)}</p>
            </div>
            <div class="arrow" aria-hidden="true">→</div>
            <div>
              <div class="code">${esc(plan.dest_code)}</div>
              <p class="when">${esc(snap.flight.arrive_time)}</p>
              <p class="where">${esc(plan.city)}</p>
            </div>
          </div>
          <div class="pass-foot">
            <span>${esc(snap.flight.via)} · ${esc(snap.flight.duration)}</span>
            <span>${esc(snap.flight.carrier)} · ${esc(snap.flight.code)}</span>
          </div>
        </div>
        <div class="pass-stub">
          <div>
            <p class="kicker">Round trip</p>
            <p class="fare">${money(snap.flight.price)}</p>
            <p class="where">${money(snap.flight.per_person)} each</p>
          </div>
          <div class="barcode" aria-hidden="true"></div>
        </div>
      </div>
      <p class="fine">Outbound shown. The fare is the round trip for the whole party. Economy, carry-on included.</p>
      <div class="choices">${plan.flights
        .map(
          (flight, index) => `
          <button type="button" class="choice ${index === plan.flight_index ? "is-on" : ""}" data-flight="${index}">
            ${esc(flight.via)} · ${esc(flight.depart_time)} · ${money(flight.price)}
          </button>`
        )
        .join("")}</div>
      <p class="scout-line">${esc(snap.wing)}</p>

      <h3 class="section-label">Hearth <span>the room</span></h3>
      <div class="key">
        <div>
          <p class="style">${esc(snap.stay.style)} · sleeps the party in ${snap.stay.units} ${snap.stay.units === 1 ? "room" : "rooms"}</p>
          <h3>${esc(snap.stay.name)}</h3>
          <p class="area">${esc(snap.stay.area)} · ${Number(snap.stay.rating).toFixed(1)}</p>
          <p class="note">${esc(snap.stay.note)}</p>
        </div>
        <div class="rate">
          <strong>${money(snap.stay.total)}</strong>
          <span>${money(snap.stay.nightly)} / night</span>
        </div>
      </div>
      <div class="choices">${plan.stays
        .map(
          (stay, index) => `
          <button type="button" class="choice ${index === plan.stay_index ? "is-on" : ""}" data-stay="${index}">
            ${esc(stay.style)} · ${esc(stay.name)} · ${money(stay.total)}
          </button>`
        )
        .join("")}</div>
      <p class="scout-line">${esc(snap.hearth)}</p>

      <h3 class="section-label">Wander <span>the days</span></h3>
      <div class="stamps">${plan.activities
        .map(
          (item) => `
          <article class="stamp">
            <small>${esc(item.area)}</small>
            <b>${esc(item.name)}</b>
            <small>${item.cost === 0 ? "Free" : money(item.cost)}</small>
          </article>`
        )
        .join("")}</div>
      <p class="scout-line">${esc(snap.wander)} ${plan.activities.map((item) => esc(item.note)).slice(0, 1).join("") ? "" : ""}</p>
      <div class="days">${plan.days
        .map(
          (day) => `
          <article class="day">
            <time>${esc(day.label)}</time>
            <div class="spine"><i></i></div>
            <div>
              <h3>${esc(day.title)}</h3>
              <ul>${day.items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
            </div>
          </article>`
        )
        .join("")}</div>
      <div class="actions">
        <button type="button" class="save" id="save-stamp">Save to passport</button>
        <button type="button" class="save alt" data-remix="Make it cheaper">Cheaper</button>
        <button type="button" class="save alt" data-remix="Nicer room">Nicer room</button>
        <button type="button" class="save alt" data-remix="More food">More food</button>
      </div>
    </article>`;
  document.title = `${plan.city} — Lark`;
  trip.scrollTop = 0;
}

async function reveal(nextPlan) {
  const token = ++renderToken;
  plan = nextPlan;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    renderPlan();
    return;
  }
  trip.innerHTML = `
    <div class="theater">
      <p class="poster-kicker">Scouts out</p>
      <h2 class="city" style="font-size:64px">${esc(plan.city)}</h2>
      <ol>
        <li data-scout="wing"><span>Wing is pricing seats</span><em>OUT</em></li>
        <li data-scout="hearth"><span>Hearth is holding rooms</span><em>WAIT</em></li>
        <li data-scout="wander"><span>Wander is saving the good parts</span><em>WAIT</em></li>
      </ol>
    </div>`;
  const steps = ["wing", "hearth", "wander"];
  for (const step of steps) {
    await wait(280);
    if (token !== renderToken) return;
    const row = trip.querySelector(`[data-scout="${step}"] em`);
    if (row) {
      row.textContent = "BACK";
      row.parentElement.classList.add("is-done");
    }
  }
  await wait(220);
  if (token !== renderToken) return;
  renderPlan();
}

function showPoster() {
  renderToken += 1;
  plan = null;
  trip.innerHTML = POSTER;
  document.title = "Lark — the trip desk";
}

function remember() {
  sessionStorage.setItem(
    "lark-desk",
    JSON.stringify({ state, plan, messages, suggestions })
  );
}

function passportItems() {
  try {
    return JSON.parse(localStorage.getItem("lark-passport") || "[]");
  } catch {
    return [];
  }
}

function drawPassport() {
  const items = passportItems();
  stampCount.textContent = String(items.length);
  if (!items.length) {
    passportList.innerHTML = `<p class="empty-pass">No stamps yet. Plan a trip, then keep it.</p>`;
    return;
  }
  passportList.innerHTML = items
    .map(
      (item, index) => `
      <button type="button" class="saved" data-open="${index}">
        <span>
          <b>${esc(item.city)}</b>
          <span>${esc(item.when)} · ${money(item.total)}</span>
        </span>
        <span>${esc(item.docket)}</span>
      </button>`
    )
    .join("");
}

async function ask(text) {
  const clean = text.trim();
  if (!clean || busy) return;
  busy = true;
  sendButton.disabled = true;
  messages.push({ role: "user", text: clean });
  renderThread();
  say.value = "";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: clean, state }),
    });
    if (!response.ok) throw new Error("closed");
    const data = await response.json();
    state = data.state;
    suggestions = data.suggestions?.length ? data.suggestions : [];
    messages.push({ role: "lark", text: data.reply });
    renderThread();
    renderChips();
    if (data.plan) {
      if (window.matchMedia("(max-width: 900px)").matches) {
        document.body.dataset.pane = "trip";
        document.querySelectorAll(".mobile-tabs button").forEach((button) => {
          button.classList.toggle("is-on", button.dataset.pane === "trip");
        });
      }
      await reveal(data.plan);
    } else {
      showPoster();
    }
    remember();
  } catch {
    messages.push({
      role: "lark",
      text: "The desk didn't answer. Give it a second and try the same line again.",
    });
    renderThread();
  } finally {
    busy = false;
    sendButton.disabled = false;
    say.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(say.value);
});

say.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.body.addEventListener("click", (event) => {
  const chip = event.target.closest("[data-chip]");
  if (chip) ask(chip.dataset.chip);
  const remix = event.target.closest("[data-remix]");
  if (remix) ask(remix.dataset.remix);
  const flight = event.target.closest("[data-flight]");
  if (flight && plan) {
    plan.flight_index = Number(flight.dataset.flight);
    renderPlan();
    remember();
  }
  const stay = event.target.closest("[data-stay]");
  if (stay && plan) {
    plan.stay_index = Number(stay.dataset.stay);
    renderPlan();
    remember();
  }
  if (event.target.closest("#save-stamp") && plan) {
    const snap = totals();
    const items = passportItems().filter((item) => item.docket !== plan.docket);
    items.unshift({
      docket: plan.docket,
      city: plan.city,
      when: `${plan.depart_label} – ${plan.ret_label}`,
      total: snap.total,
      state,
      plan,
    });
    localStorage.setItem("lark-passport", JSON.stringify(items.slice(0, 12)));
    drawPassport();
    messages.push({ role: "lark", text: `${plan.city} is in the passport. It'll be here when you come back.` });
    renderThread();
    remember();
  }
  const saved = event.target.closest("[data-open]");
  if (saved) {
    const item = passportItems()[Number(saved.dataset.open)];
    if (!item) return;
    state = item.state;
    suggestions = ["Make it cheaper", "Nicer room", "More food", "Shorter"];
    messages.push({ role: "lark", text: `Pulled ${item.city} back out of the passport.` });
    renderThread();
    renderChips();
    renderPlanFrom(item.plan);
    passport.hidden = true;
    if (window.matchMedia("(max-width: 900px)").matches) document.body.dataset.pane = "trip";
    remember();
  }
});

function renderPlanFrom(savedPlan) {
  plan = savedPlan;
  renderPlan();
}

document.querySelector("#new-trip").addEventListener("click", () => {
  state = null;
  messages = [{ role: "lark", text: INTRO }];
  suggestions = STARTER_CHIPS.slice();
  showPoster();
  renderThread();
  renderChips();
  sessionStorage.removeItem("lark-desk");
  document.body.dataset.pane = "desk";
});

document.querySelector("#open-passport").addEventListener("click", () => {
  drawPassport();
  passport.hidden = false;
});
document.querySelector("#close-passport").addEventListener("click", () => {
  passport.hidden = true;
});
passport.addEventListener("click", (event) => {
  if (event.target === passport) passport.hidden = true;
});

document.querySelectorAll(".mobile-tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    document.body.dataset.pane = button.dataset.pane;
    document.querySelectorAll(".mobile-tabs button").forEach((other) => {
      other.classList.toggle("is-on", other === button);
    });
  });
});

try {
  const saved = JSON.parse(sessionStorage.getItem("lark-desk") || "null");
  if (saved?.messages?.length) {
    messages = saved.messages;
    state = saved.state;
    suggestions = saved.suggestions || STARTER_CHIPS.slice();
    if (saved.plan) plan = saved.plan;
  }
} catch {
  /* a fresh desk */
}

renderThread();
renderChips();
drawPassport();
if (plan) renderPlan();
