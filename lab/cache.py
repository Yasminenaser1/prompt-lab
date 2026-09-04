import hashlib
import json
import sqlite3
from datetime import datetime, timezone

DB_PATH = "lab.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_cache():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS cache (
            key      TEXT PRIMARY KEY,
            model    TEXT,
            prompt   TEXT,
            response TEXT,
            created  TEXT)""")


def make_key(model, prompt, temperature):
    blob = json.dumps([model, prompt, temperature], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def cached_call(prompt, model, temperature=0.0, call_fn=None):
    """Return (response_text, was_cache_hit)."""
    init_cache()
    key = make_key(model, prompt, temperature)

    with _connect() as conn:
        row = conn.execute(
            "SELECT response FROM cache WHERE key = ?", (key,)
        ).fetchone()
    if row:
        return row[0], True

    if call_fn is None:
        from lab.runner import call_model as call_fn
    response = call_fn(prompt, model=model)

    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?, ?)",
            (key, model, prompt, response,
             datetime.now(timezone.utc).isoformat()),
        )
    return response, False


def cache_stats():
    init_cache()
    with _connect() as conn:
        n = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    return n
