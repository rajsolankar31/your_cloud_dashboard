"""Local credential store. Values are written to a git-ignored JSON file on this machine
(plain text, so protect your user account) and are never returned by the API."""
import json
import os
from pathlib import Path

FIELDS = {
    "vercel": ["VERCEL_TOKEN", "VERCEL_TEAM_ID"],
    "google": ["GOOGLE_CLOUD_PROJECT_ID", "GOOGLE_APPLICATION_CREDENTIALS"],
    "oracle": [],
}
ALLOWED = {k for v in FIELDS.values() for k in v} | {"USE_MOCK"}
SECRET = {"VERCEL_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS"}


def _path() -> Path:
    return Path(os.getenv("SECRETS_PATH", ".secrets.json"))


def _read() -> dict:
    try:
        return json.loads(_path().read_text())
    except Exception:
        return {}


def load() -> None:
    for k, v in _read().items():
        if k in ALLOWED:
            os.environ[k] = str(v)


def save(values: dict) -> None:
    data = _read()
    for k, v in values.items():
        if k not in ALLOWED:
            continue
        if v in ("", None):
            data.pop(k, None)
            os.environ.pop(k, None)
        else:
            data[k] = str(v)
            os.environ[k] = str(v)
    _path().write_text(json.dumps(data))


def fields(provider: str) -> list[dict]:
    return [{"name": k, "set": bool(os.getenv(k)), "secret": k in SECRET} for k in FIELDS.get(provider, [])]
