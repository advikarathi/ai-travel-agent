"""The model Lark thinks with. Any OpenAI-compatible chat API works.

Settings come from, in order: .streamlit/secrets.toml, environment
variables, then .env. Point LARK_LLM_BASE_URL and LARK_LLM_MODEL at a
free provider (OpenRouter, Groq, a local Ollama) if you like.
"""

from __future__ import annotations

import json
import os
import re
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ("LARK_LLM_API_KEY", "LARK_LLM_BASE_URL", "LARK_LLM_MODEL", "LARK_LLM_FALLBACK_MODEL")
# Waits (seconds) between tries when the provider is busy (5xx) or rate-limited (429).
BACKOFF = (2, 4, 8)
# How long one request may take, and how long one question may take in total
# (all retries and the fallback model included), so the app never hangs.
REQUEST_TIMEOUT = 20
TOTAL_BUDGET = 50
DEFAULTS = {"LARK_LLM_BASE_URL": "https://api.openai.com/v1", "LARK_LLM_MODEL": "gpt-4o-mini"}


class LLMError(Exception):
    """Something the person using the app should be told about."""


class LLMNotConfigured(LLMError):
    pass


class LLMRateLimited(LLMError):
    pass


class LLMBadOutput(LLMError):
    """The model answered, but not with usable JSON. Callers fall back to rules."""


def _from_secrets() -> dict:
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return {key: str(data[key]) for key in KEYS if data.get(key)}


def _from_dotenv() -> dict:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if key.strip() in KEYS and value:
            found[key.strip()] = value
    return found


def settings() -> dict:
    secrets, dotenv = _from_secrets(), _from_dotenv()
    resolved = {}
    for key in KEYS:
        resolved[key] = secrets.get(key) or os.environ.get(key) or dotenv.get(key) or DEFAULTS.get(key, "")
    return resolved


def is_configured() -> bool:
    return bool(settings()["LARK_LLM_API_KEY"])


def parse_json(text: str) -> dict:
    """Pull one JSON object out of a reply, tolerating ```json fences and chatter."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise LLMBadOutput("The model did not return JSON.")
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise LLMBadOutput(f"The model returned broken JSON: {error}") from error
    if not isinstance(value, dict):
        raise LLMBadOutput("The model returned JSON, but not an object.")
    return value


def _detail(error) -> str:
    """The provider's own explanation, short enough to show in the app."""
    body = getattr(error, "body", None)
    message = ""
    if isinstance(body, dict):
        inner = body.get("error", body)
        message = inner.get("message") if isinstance(inner, dict) else str(inner)
    message = message or getattr(error, "message", "") or str(error)
    return " ".join(str(message).split())[:300]


class _Busy(Exception):
    """The provider is overloaded or rate-limiting: worth waiting and retrying."""

    def __init__(self, status: int, retry_after: str | None = None):
        super().__init__(status)
        self.status = status
        self.retry_after = retry_after


class LLM:
    def __init__(
        self, api_key: str, base_url: str, model: str, fallback_model: str = "", sleep=time.sleep, clock=time.monotonic
    ):
        from openai import OpenAI

        self.model = model
        self.fallback_model = fallback_model if fallback_model and fallback_model != model else ""
        self.sleep = sleep
        self.clock = clock
        # Retries are handled in _create so busy errors get real waits and a fallback model.
        # Some gateways (LiteLLM, Anthropic-style) read the key from x-api-key instead of
        # the Authorization header, so send it both ways.
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            max_retries=0,
            timeout=REQUEST_TIMEOUT,
            default_headers={"x-api-key": api_key},
        )
        self.send_temperature = True

    def _call(self, model: str, messages: list) -> str:
        """One request. Busy errors (5xx, 429) raise _Busy; others raise LLMError."""
        import openai

        extra = {"temperature": 0.3} if self.send_temperature else {}
        try:
            response = self.client.chat.completions.create(model=model, messages=messages, **extra)
        except openai.BadRequestError as error:
            detail = _detail(error)
            # Newer models on some gateways refuse sampling settings; ask again without them.
            if self.send_temperature and ("temperature" in detail.lower() or "sampling" in detail.lower()):
                self.send_temperature = False
                return self._call(model, messages)
            if "model" in detail.lower() and ("invalid" in detail.lower() or "not" in detail.lower()):
                raise _Busy(404) from error  # unknown or not-allowed model: try the fallback
            raise LLMError(f"The LLM provider refused the request (400): {detail}") from error
        except openai.RateLimitError as error:
            wait = None
            if getattr(error, "response", None) is not None:
                wait = error.response.headers.get("retry-after")
            raise _Busy(429, wait) from error
        except openai.AuthenticationError as error:
            raise LLMError("The LLM provider rejected LARK_LLM_API_KEY. Check the key in .streamlit/secrets.toml or .env.") from error
        except openai.NotFoundError as error:
            raise _Busy(404) from error  # an unknown model: the fallback may still work
        except openai.APITimeoutError as error:
            raise _Busy(504) from error
        except openai.APIConnectionError as error:
            raise LLMError("Couldn't reach the LLM provider. Check your internet connection.") from error
        except openai.APIStatusError as error:
            if error.status_code >= 500:
                raise _Busy(error.status_code) from error
            raise LLMError(f"The LLM provider returned an error ({error.status_code}): {_detail(error)}") from error
        return (response.choices[0].message.content or "") if response.choices else ""

    def _create(self, messages: list) -> str:
        """Try the main model with waits in between, then the fallback model once."""
        last: _Busy | None = None
        deadline = self.clock() + TOTAL_BUDGET
        models = [self.model] + ([self.fallback_model] if self.fallback_model else [])
        for model in models:
            waits = BACKOFF if model == self.model else (2,)
            for attempt in range(len(waits) + 1):
                # Leave room for the fallback model before giving up on the main one.
                if self.clock() >= deadline:
                    break
                try:
                    return self._call(model, messages)
                except _Busy as busy:
                    last = busy
                    # Unknown model or a request that timed out: go straight to the fallback.
                    if busy.status in (404, 504) or attempt == len(waits):
                        break
                    if self.clock() + waits[attempt] + REQUEST_TIMEOUT >= deadline and model != models[-1]:
                        break  # not enough time for another try here; use the fallback instead
                    self.sleep(waits[attempt])
        if last is None:
            raise LLMError("The LLM provider took too long to answer. Try again in a minute.")
        if last.status == 404:
            names = " or ".join(f"'{m}'" for m in [self.model, self.fallback_model] if m)
            raise LLMError(f"The provider doesn't know the model {names}. Check LARK_LLM_MODEL and LARK_LLM_BASE_URL.")
        if last.status == 429:
            hint = f" in about {last.retry_after} seconds" if last.retry_after else " in a minute"
            raise LLMRateLimited(f"The model is rate-limited right now (common on free tiers). Try again{hint}.")
        if last.status == 504:
            also = ", even with the backup model" if self.fallback_model else ""
            raise LLMError(f"The LLM provider took too long to answer{also}. Try again in a minute.")
        raise LLMError(f"The LLM provider is overloaded right now (error {last.status}), even after retrying. Try again in a minute.")

    def chat_json(self, task: str, system: str, payload: dict) -> dict:
        messages = [
            {"role": "system", "content": system + "\nReply with one JSON object and nothing else."},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        last_error: LLMBadOutput | None = None
        for _attempt in range(2):
            content = self._create(messages)
            try:
                return parse_json(content)
            except LLMBadOutput as error:
                last_error = error
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "That was not valid JSON. Send only the JSON object."})
        assert last_error is not None
        raise last_error


_CACHED: dict[tuple, LLM] = {}


def get_llm() -> LLM:
    config = settings()
    if not config["LARK_LLM_API_KEY"]:
        raise LLMNotConfigured(
            "No LLM key found. Add LARK_LLM_API_KEY to .streamlit/secrets.toml "
            "(copy .streamlit/secrets.toml.example) or to .env, then reload."
        )
    signature = tuple(config[key] for key in KEYS)
    if signature not in _CACHED:
        _CACHED[signature] = LLM(
            config["LARK_LLM_API_KEY"],
            config["LARK_LLM_BASE_URL"],
            config["LARK_LLM_MODEL"],
            config["LARK_LLM_FALLBACK_MODEL"],
        )
    return _CACHED[signature]
