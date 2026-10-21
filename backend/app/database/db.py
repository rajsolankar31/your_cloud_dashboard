import contextlib
import sqlite3

from ..config import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS resources (
  id TEXT PRIMARY KEY, provider TEXT NOT NULL, resource_type TEXT NOT NULL,
  name TEXT NOT NULL, status TEXT NOT NULL, region TEXT,
  last_checked TEXT NOT NULL, stale INTEGER NOT NULL DEFAULT 0, meta TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT NOT NULL,
  status TEXT NOT NULL, checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, provider TEXT NOT NULL,
  started_at TEXT NOT NULL, ok INTEGER NOT NULL, count INTEGER NOT NULL DEFAULT 0, error TEXT
);
CREATE TABLE IF NOT EXISTS details (
  resource_id TEXT PRIMARY KEY, notes TEXT, tags TEXT, owner TEXT, monthly_cost REAL
);
CREATE TABLE IF NOT EXISTS budgets (provider TEXT PRIMARY KEY, monthly_limit REAL NOT NULL);
CREATE TABLE IF NOT EXISTS actions (
  id TEXT PRIMARY KEY, provider TEXT NOT NULL, resource_id TEXT NOT NULL,
  resource_name TEXT NOT NULL, action TEXT NOT NULL, status TEXT NOT NULL,
  impact TEXT, requested_at TEXT NOT NULL, confirmed_at TEXT, finished_at TEXT, detail TEXT
);
"""


@contextlib.contextmanager
def conn():
    c = sqlite3.connect(db_path())
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
