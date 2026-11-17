"""Free extras for a plan: weather, photos and map points. No API keys.

- Weather: Open-Meteo. A real forecast for trips in the next 16 days; for later
  trips, what the same dates were like last year, labelled as such.
- Photos and map points: Wikipedia. One search per place returns its lead photo
  and its coordinates. A result is used only if its title shares a distinctive
  word with the place's name and it sits near the city, because a wrong photo is
  worse than none.

Every lookup has a short time limit and a disk cache. If anything fails, the
plan simply shows without that extra.
"""

from __future__ import annotations

import json
import math
import re
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "extras_cache.json"
TIMEOUT = 8
USER_AGENT = "Lark-trip-planner/1.0 (student project; https://github.com/advikarathi/ai-travel-agent)"
FORECAST_DAYS = 16
NEAR_KM = 90  # cities' coordinates are their airports, so allow the drive in

# Open-Meteo weather codes -> a short word and whether it means rain or snow.
WEATHER_WORDS = [
    ((0,), "Sunny", False),
    ((1, 2), "Partly cloudy", False),
    ((3,), "Cloudy", False),
    ((45, 48), "Fog", False),
    ((51, 53, 55, 56, 57), "Drizzle", True),
    ((61, 63, 65, 66, 67, 80, 81, 82), "Rain", True),
    ((71, 73, 75, 77, 85, 86), "Snow", True),
    ((95, 96, 99), "Storms", True),
]

STOPWORDS = {
    "the", "a", "an", "of", "and", "in", "at", "on", "to", "from", "for", "with", "after", "early", "late",
    "walk", "tour", "afternoon", "morning", "evening", "night", "dark", "dusk", "day", "trip", "lunch",
    "dinner", "slot", "entry", "visit", "park", "market", "museum", "de", "da", "do", "la", "le", "el",
}


# ---- cache + http ------------------------------------------------------------------
def _cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _remember(key: str, value) -> None:
    cache = _cache()
    cache[key] = {"at": time.time(), "value": value}
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass


def _recall(key: str, max_age_hours: float):
    hit = _cache().get(key)
    if hit and time.time() - hit["at"] < max_age_hours * 3600:
        return True, hit["value"]
    return False, None


def _get_json(url: str, params: dict) -> dict | None:
    try:
        import httpx

        response = httpx.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


# ---- weather -----------------------------------------------------------------------
def _describe(code) -> tuple[str, bool]:
    for codes, word, wet in WEATHER_WORDS:
        if code in codes:
            return word, wet
    return "Mixed", False


def parse_weather(data: dict, kind: str) -> list[dict]:
    daily = (data or {}).get("daily") or {}
    days = []
    for index, when in enumerate(daily.get("time") or []):
        def pick(name):
            values = daily.get(name) or []
            return values[index] if index < len(values) else None

        high, low, code = pick("temperature_2m_max"), pick("temperature_2m_min"), pick("weather_code")
        if high is None or low is None:
            continue
        word, wet = _describe(code)
        chance = pick("precipitation_probability_max")
        rain_mm = pick("precipitation_sum")
        if chance is not None:
            wet = wet or chance >= 50
        elif rain_mm is not None:
            wet = wet or rain_mm >= 2
        days.append(
            {
                "date": when,
                "high": round(high),
                "low": round(low),
                "summary": word,
                "rain_chance": chance,
                "rain_mm": round(rain_mm, 1) if isinstance(rain_mm, (int, float)) else None,
                "wet": bool(wet),
                "kind": kind,
            }
        )
    return days


def weather(lat: float, lon: float, depart: str, nights: int, today: date | None = None) -> list[dict]:
    """One entry per trip day: high/low (°F), a word, and whether it's wet.

    kind = "forecast" (real forecast) or "last_year" (same dates a year earlier).
    """
    today = today or date.today()
    start = date.fromisoformat(depart)
    end = start + timedelta(days=max(0, nights - 1))
    key = f"weather:{lat:.2f},{lon:.2f}:{start}:{end}"
    found, value = _recall(key, 6)
    if found:
        return value
    common = {"latitude": lat, "longitude": lon, "temperature_unit": "fahrenheit", "timezone": "auto"}
    if (end - today).days < FORECAST_DAYS:
        data = _get_json(
            "https://api.open-meteo.com/v1/forecast",
            {**common, "start_date": start.isoformat(), "end_date": end.isoformat(),
             "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"},
        )
        days = parse_weather(data, "forecast") if data else []
    else:
        try:
            past_start, past_end = start.replace(year=start.year - 1), end.replace(year=end.year - 1)
        except ValueError:  # Feb 29
            past_start, past_end = start - timedelta(days=365), end - timedelta(days=365)
        data = _get_json(
            "https://archive-api.open-meteo.com/v1/archive",
            {**common, "start_date": past_start.isoformat(), "end_date": past_end.isoformat(),
             "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"},
        )
        days = parse_weather(data, "last_year") if data else []
        # Show them on this year's dates.
        for offset, day in enumerate(days):
            day["date"] = (start + timedelta(days=offset)).isoformat()
    if days:
        _remember(key, days)
    return days


# ---- Wikipedia photos and coordinates --------------------------------------------------
def _km(lat1, lon1, lat2, lon2) -> float:
    rad = math.radians
    a = math.sin(rad(lat2 - lat1) / 2) ** 2 + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(rad(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zà-ÿ0-9']+", text.lower()) if len(w) > 2 and w not in STOPWORDS}


def best_page(pages: list[dict], name: str, city_lat: float, city_lon: float) -> dict | None:
    """The search result whose title covers most of the place's name, near the city.

    At least half of the name's distinctive words must be in the title, so
    "Pastéis de Belém" gets the bakery, not Belém Tower next door.
    """
    wanted = _words(name)
    if not wanted:
        return None
    best, best_score = None, 0.0
    for order, page in enumerate(pages):
        share = len(wanted & _words(page.get("title", ""))) / len(wanted)
        if share < 0.5:
            continue
        coords = (page.get("coordinates") or [{}])[0]
        lat, lon = coords.get("lat"), coords.get("lon")
        if lat is None or lon is None or _km(city_lat, city_lon, lat, lon) > NEAR_KM:
            continue
        score = share - order / 100  # ties go to the search's own order
        if score > best_score:
            best_score = score
            best = {
                "title": page["title"],
                "lat": lat,
                "lon": lon,
                "photo": (page.get("thumbnail") or {}).get("source"),
                "url": "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_"),
            }
    return best


def place(name: str, city: str, city_lat: float, city_lon: float) -> dict | None:
    key = f"wiki:{name}|{city}"
    found, value = _recall(key, 24 * 30)
    if found:
        return value
    data = _get_json(
        "https://en.wikipedia.org/w/api.php",
        {
            "action": "query", "format": "json", "formatversion": 2,
            "generator": "search", "gsrsearch": f"{name} {city}", "gsrlimit": 5,
            "prop": "pageimages|coordinates", "piprop": "thumbnail", "pithumbsize": 640, "colimit": 5,
        },
    )
    if data is None:
        return None  # network trouble: try again next time, don't cache
    pages = sorted((data.get("query") or {}).get("pages") or [], key=lambda p: p.get("index", 99))
    result = best_page(pages, name, city_lat, city_lon)
    _remember(key, result)
    return result


def city_photo(city: str) -> dict | None:
    key = f"wiki-city:{city}"
    found, value = _recall(key, 24 * 30)
    if found:
        return value
    data = _get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{city.replace(' ', '_')}", {})
    if data is None:
        return None
    image = (data.get("originalimage") or data.get("thumbnail") or {}).get("source")
    result = {"photo": image, "url": (data.get("content_urls") or {}).get("desktop", {}).get("page")} if image else None
    _remember(key, result)
    return result


# ---- everything a plan's screen needs ---------------------------------------------------
def enrich(plan: dict, city_lat: float, city_lon: float, budget_seconds: float = 20) -> dict:
    """Photos and map points for the plan's city and activities, within a time budget."""
    started = time.time()
    out = {"city_photo": city_photo(plan["city"]), "places": {}}
    for activity in plan["activities"]:
        if time.time() - started > budget_seconds:
            break
        found = place(activity["name"], plan["city"], city_lat, city_lon)
        if not found:
            # Fall back to the neighbourhood for the map (never for the photo).
            area = place(activity["area"], plan["city"], city_lat, city_lon)
            if area:
                found = {**area, "photo": None, "approximate": True}
        if found:
            out["places"][activity["name"]] = found
    return out
