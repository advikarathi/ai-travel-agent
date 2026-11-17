# Lark

A budget-first trip planner built in Python and Streamlit. Tell Lark where you're going (or ask where you *can* go), when, who's coming and what the whole trip may cost. It picks a flight, a place to stay and what to do each day, keeps it all inside the budget, and links every item to the real booking page.

Everything it uses is free: an OpenAI-compatible LLM (the school's Claude server or Gemini's free tier), live fares from Google Flights through the open-source `fast-flights` library, weather from Open-Meteo, and photos and map points from Wikipedia. No paid APIs.

## What it does

- **Plans a trip from one sentence.** "Two of us, Boston to Lisbon, 5 nights in June, $3200."
- **Finds a destination.** "Where can we go from Boston for $2,500 in April?" Lark prices all 10 cities for your exact trip, and the LLM picks one and explains why, showing the others it compared.
- **Live flight fares.** Real round-trip prices from Google Flights for your dates. Hotel and activity prices are Lark's estimates, labelled as such, with links to the live rates.
- **Weather-aware days.** A real forecast for trips in the next 16 days, otherwise last year's weather on the same dates. The LLM puts indoor plans on the wet days.
- **Plans around you.** Pace, how much walking, and food needs (sidebar, under *About you*).
- **Answers questions about the trip.** "What should I pack?", "Is this too rushed?", "Why not the nonstop?" are answered from the plan, without replanning it.
- **Photos and maps.** Destination and landmark photos from Wikipedia, and a map of each day's stops.
- **Take it with you.** Download the plan as a PDF or add it to your calendar (.ics), and save trips to a CSV file.

## How it works

Each chat turn goes through `lark.agent.respond(message, state, current_plan)`:

1. **The LLM reads the request** and turns it into trip fields (origin, destination, dates, budget, travelers, vibe), or recognises a question about the plan on screen and answers it. A rule-based parser runs first and fills in what the model leaves out.
2. **Lark asks for whatever is missing**, one question at a time. It never plans without a budget.
3. **If no city was named, the LLM picks one** from all 10, each priced for this exact trip on estimates (no live lookups while comparing).
4. **Code gathers the options**: live Google Flights fares (or estimates), stays and activities from `lark/catalog.py`, and the weather for each day.
5. **The LLM chooses and writes**: one flight, one stay, the activities, a day-by-day plan matched to the weather and the traveler's profile, and the trade-offs it made.
6. **Code checks the choice.** Totals are recomputed from the options. Over budget: the priciest extras are trimmed. Anything invented: the rule-based plan is used instead, and the app says so.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then set LARK_LLM_API_KEY, LARK_LLM_BASE_URL, LARK_LLM_MODEL
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open http://localhost:8501.

### LLM settings

Read from `.streamlit/secrets.toml`, then environment variables, then `.env`:

| Setting | Meaning |
|---|---|
| `LARK_LLM_API_KEY` | API key (required) |
| `LARK_LLM_BASE_URL` | Any OpenAI-compatible endpoint, such as the school's Claude server or `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `LARK_LLM_MODEL` | Model name at that endpoint |
| `LARK_LLM_FALLBACK_MODEL` | Optional backup model, used when the main one is busy, slow or unknown |

## Tests and evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest            # 50 tests, fake model, no network, no cost
.\.venv\Scripts\python.exe evaluate.py           # the 10-request evaluation set against the real model
.\.venv\Scripts\python.exe evaluate.py --estimates   # same, without live fares (faster)
```

`evaluate.py` runs 10 realistic requests (including a destination search and a deliberately tight budget) and reports how many plans came back, stayed under budget, added up, used the LLM's own pick and got live fares, plus the time per plan. Results are saved to `data/eval_results.csv`.

## Deploy (Streamlit Community Cloud, free)

1. Push this repo to GitHub (`.env` and `.streamlit/secrets.toml` are ignored, so keys stay off GitHub).
2. At [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, choose **Create app**, pick `advikarathi/ai-travel-agent`, branch `main`, main file `app.py`, and Python 3.12 under **Advanced settings**.
3. In **Advanced settings → Secrets**, paste the LLM settings in TOML form:
   ```toml
   LARK_LLM_API_KEY = "..."
   LARK_LLM_BASE_URL = "..."
   LARK_LLM_MODEL = "..."
   LARK_LLM_FALLBACK_MODEL = "..."
   ```
4. Deploy, and share the link.

On a hosted server, Google Flights may not answer requests from a data centre; Lark then uses estimated fares and says so. The school's Claude server may also only accept requests from campus or VPN; if so, use Gemini's free tier for the hosted version. Saved trips on the hosted app reset when it restarts.

## Layout

```
app.py              Streamlit app
evaluate.py         10-request evaluation set
lark/agent.py       respond(): LLM reading, destination pick, planning, questions, budget checks
lark/llm.py         OpenAI-compatible client, retries, backup model
lark/parse.py       rule-based parser and follow-up questions
lark/plan.py        priced options, city comparison, rule-based planner
lark/catalog.py     built-in inventory (10 destinations, 20 origins)
lark/live.py        live Google Flights fares (fast-flights), cached
lark/extras.py      weather (Open-Meteo), photos and map points (Wikipedia), cached
lark/look.py        the travel-style layout
lark/links.py       booking and map links
lark/export.py      PDF and calendar export
lark/storage.py     saved trips CSV
server.py, static/  the earlier FastAPI version
tests/              pytest suite (fake model, no network)
```

## Limits

- Hotel and activity prices are estimates; there's no free, allowed source for live hotel rates.
- 10 destinations, each with a hand-picked inventory of stays and activities.
- Google Flights can change its page, which would stop live fares until `fast-flights` is updated; estimates take over meanwhile.
