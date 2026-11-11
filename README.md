# Lark

A budget-first trip desk. Tell Lark where you're going, when, who's coming, and what the whole trip may cost. It plans flights, a place to stay, and a day-by-day itinerary that fits the budget, using its built-in inventory of 10 destinations.

## How it works

Each chat turn goes through `lark.agent.respond(message, state)`:

1. **The LLM reads the request.** It turns free text ("me and my partner, Paris, mid May, about 3k") into structured fields: origin, destination, dates, budget, travelers, vibe. A rule-based parser runs first and fills in anything the model leaves out.
2. **Lark asks for whatever is missing**, one question at a time. It never plans without a budget.
3. **Code prices the options.** For the destination it builds 3 flight options, 4 stays, and 6 activities from the inventory in `lark/catalog.py`.
4. **The LLM chooses and writes.** It picks a flight, a stay, and activities that fit the budget and vibe, writes the day-by-day plan, and explains the trade-offs.
5. **Code checks the choice.** Totals are recomputed from the inventory. If the pick goes over budget, the priciest extras are trimmed. If it names something that isn't in the inventory, the rule-based plan is used instead and the app says so.

All prices are **desk estimates** from the built-in inventory, not live fares or bookings. (Live fares came from Amadeus, which shut down its self-service API in July 2026, so that code was removed.)

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then set LARK_LLM_API_KEY
.\.venv\Scripts\streamlit.exe run app.py
```

Then open http://localhost:8501.

### LLM settings

The LLM is required. Lark reads these from `.streamlit/secrets.toml`, then from environment variables, then from `.env`:

| Setting | Meaning | Default |
|---|---|---|
| `LARK_LLM_API_KEY` | API key (required) | none |
| `LARK_LLM_BASE_URL` | Any OpenAI-compatible endpoint | `https://api.openai.com/v1` |
| `LARK_LLM_MODEL` | Model name at that endpoint | `gpt-4o-mini` |

To use a free model, point `LARK_LLM_BASE_URL` and `LARK_LLM_MODEL` at a provider such as Groq, OpenRouter (models tagged `:free`), or a local Ollama. Check the provider's current model list for exact names. Free tiers often rate-limit; the app shows a "Try again" button when that happens.

If no key is set, the app shows a message explaining how to add one instead of a chat.

## The app

- **Chat**: type a trip in plain English, or tap a suggestion.
- **Sidebar**: budget, dates, travelers, and vibe. Anything you change there goes into the next plan; press **Update plan** to re-plan straight away.
- **Save trip**: adds the plan to `data/saved_trips.csv`. The **Saved trips** section at the bottom lists them.

## Other entry points

- The old web UI still works: `.\.venv\Scripts\python.exe -m uvicorn server:app --port 8765` (it also needs the key, in `.env`).
- Tests use a fake LLM, so they need no key: `.\.venv\Scripts\python.exe -m pytest`.

## Layout

```
app.py            Streamlit app
server.py         FastAPI app + static/ web UI
lark/agent.py     respond(): LLM extraction, LLM planning, budget checks
lark/llm.py       OpenAI-compatible client, settings, error handling
lark/parse.py     rule-based parser and follow-up questions
lark/plan.py      priced flight/stay/activity options, rule-based planner
lark/catalog.py   built-in inventory (10 destinations, 20 origins)
lark/storage.py   saved trips CSV
```
