import json
import sqlite3
from datetime import datetime, timezone

DB_PATH = "lab.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            task         TEXT,
            model        TEXT,
            prompt_text  TEXT,
            split        TEXT,
            mean_score   REAL,
            candidate_id INTEGER,
            started_at   TEXT,
            notes        TEXT)""")

        conn.execute("""CREATE TABLE IF NOT EXISTS case_results (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id    INTEGER,
            case_id   TEXT,
            predicted TEXT,
            score     REAL,
            parse_ok  INTEGER,
            FOREIGN KEY (run_id) REFERENCES runs(id))""")

        conn.execute("""CREATE TABLE IF NOT EXISTS candidates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task        TEXT,
            prompt_text TEXT,
            parent_id   INTEGER,
            optimizer   TEXT,
            dev_score   REAL,
            created_at  TEXT,
            FOREIGN KEY (parent_id) REFERENCES candidates(id))""")


def save_run(task, model, prompt_text, split, mean_score,
             results, candidate_id=None, notes=None):
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs (task, model, prompt_text, split, mean_score, "
            "candidate_id, started_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task, model, prompt_text, split, mean_score, candidate_id,
             datetime.now(timezone.utc).isoformat(), notes),
        )
        run_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO case_results (run_id, case_id, predicted, score, "
            "parse_ok) VALUES (?, ?, ?, ?, ?)",
            [(run_id, r["case_id"],
              json.dumps(r.get("predicted")) if r.get("predicted") else None,
              r["score"], 1 if r["parse_ok"] else 0) for r in results],
        )
    return run_id


def save_candidate(task, prompt_text, optimizer,
                   parent_id=None, dev_score=None):
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO candidates (task, prompt_text, parent_id, optimizer, "
            "dev_score, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task, prompt_text, parent_id, optimizer, dev_score,
             datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def set_candidate_score(candidate_id, dev_score):
    with _connect() as conn:
        conn.execute("UPDATE candidates SET dev_score = ? WHERE id = ?",
                     (dev_score, candidate_id))


def history(task=None, limit=50):
    init_db()
    q = ("SELECT id, split, mean_score, candidate_id, started_at "
         "FROM runs {} ORDER BY id DESC LIMIT ?")
    with _connect() as conn:
        if task:
            return conn.execute(q.format("WHERE task = ?"),
                                (task, limit)).fetchall()
        return conn.execute(q.format(""), (limit,)).fetchall()
