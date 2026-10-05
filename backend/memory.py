"""Persistent memory — the Personal AI core.

A patient's case does not live inside one chat. It lives in SQLite and outlives
the session: the diagnosis, the proposed operation and the data category it maps
to, the named surgeon and hospital, how far they will travel, their network, every
question asked and answer given, and a dated journal of what the agent has done.

On top of that sits a searchable memory of past turns, embedded with a Token
Factory embedding model so the agent can recall the relevant history ('what did
the surgeon say about his numbers?') rather than re-reading everything. Embeddings
are cached on disk by text hash, so seeding computes each one once and a judge's
click costs nothing.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
import os
DB_PATH = Path(os.environ.get("DATA_DIR", HERE)) / "second_opinion.db"
EMB_CACHE = HERE / "cache" / "embeddings.json"
EMBED_MODEL = "Qwen/Qwen3-Embedding-8B"  # the catalogue's embedding model (non-NVIDIA, for recall)


# ── schema ───────────────────────────────────────────────────────────────────
def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    con = connect()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS patient_case (
            id            TEXT PRIMARY KEY,
            label         TEXT NOT NULL,
            region        TEXT NOT NULL,          -- US or UK
            diagnosis     TEXT,
            operation     TEXT,                   -- the patient's words
            operation_key TEXT,                   -- mapped procedure (evidence/data key)
            dataset       TEXT,                   -- which real dataset applies
            surgeon       TEXT,
            hospital      TEXT,                   -- hospital named in the letter
            network       TEXT,                   -- insurance / NHS region
            travel_miles  INTEGER,
            consultation  TEXT,                   -- ISO date of the next appointment
            created_at    REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id    TEXT NOT NULL,
            role       TEXT NOT NULL,             -- patient | agent
            kind       TEXT NOT NULL,             -- message | question | answer | finding | action
            text       TEXT NOT NULL,
            embedding  TEXT,                       -- JSON array, or null
            created_at REAL NOT NULL,
            FOREIGN KEY (case_id) REFERENCES patient_case(id)
        );
        """
    )
    con.commit()
    con.close()


# ── embeddings, cached by text hash ──────────────────────────────────────────
def _load_cache() -> dict[str, list[float]]:
    if EMB_CACHE.exists():
        try:
            return json.loads(EMB_CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict[str, list[float]]) -> None:
    EMB_CACHE.parent.mkdir(exist_ok=True)
    EMB_CACHE.write_text(json.dumps(cache))


def _key(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:24]


def embed(text: str, *, allow_live: bool = True) -> list[float] | None:
    """Vector for a piece of text. Served from the on-disk cache when seen before;
    otherwise computed live (if allowed) and cached. Returns None if it has never
    been embedded and a live call is not permitted — the caller then falls back to
    recency, so the app never breaks offline."""
    cache = _load_cache()
    k = _key(text)
    if k in cache:
        return cache[k]
    if not allow_live:
        return None
    from nemotron import client
    resp = client().embeddings.create(model=EMBED_MODEL, input=text[:4000])
    vec = resp.data[0].embedding
    cache[k] = vec
    _save_cache(cache)
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ── case CRUD ────────────────────────────────────────────────────────────────
def create_case(case: dict[str, Any]) -> None:
    con = connect()
    con.execute(
        """INSERT OR REPLACE INTO patient_case
           (id,label,region,diagnosis,operation,operation_key,dataset,surgeon,
            hospital,network,travel_miles,consultation,created_at)
           VALUES (:id,:label,:region,:diagnosis,:operation,:operation_key,:dataset,
            :surgeon,:hospital,:network,:travel_miles,:consultation,:created_at)""",
        {**{"diagnosis": None, "operation": None, "operation_key": None,
            "dataset": None, "surgeon": None, "hospital": None, "network": None,
            "travel_miles": None, "consultation": None,
            "created_at": time.time()}, **case},
    )
    con.commit()
    con.close()


def get_case(case_id: str) -> dict | None:
    con = connect()
    row = con.execute("SELECT * FROM patient_case WHERE id=?", (case_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def list_cases() -> list[dict]:
    con = connect()
    rows = con.execute("SELECT * FROM patient_case ORDER BY created_at").fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── memory read/write ────────────────────────────────────────────────────────
def add_memory(case_id: str, role: str, kind: str, text: str, *,
               allow_live_embed: bool = True) -> int:
    vec = embed(text, allow_live=allow_live_embed)
    con = connect()
    cur = con.execute(
        "INSERT INTO memory (case_id,role,kind,text,embedding,created_at) "
        "VALUES (?,?,?,?,?,?)",
        (case_id, role, kind, text, json.dumps(vec) if vec else None, time.time()),
    )
    con.commit()
    mid = cur.lastrowid
    con.close()
    return mid


def timeline(case_id: str) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT id,role,kind,text,created_at FROM memory WHERE case_id=? ORDER BY id",
        (case_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def recall(case_id: str, query: str, k: int = 4, *,
           allow_live_embed: bool = True) -> list[dict]:
    """The memory in this case most relevant to the query, by embedding similarity.
    Falls back to most-recent if the query cannot be embedded offline."""
    con = connect()
    rows = con.execute(
        "SELECT id,role,kind,text,embedding,created_at FROM memory WHERE case_id=?",
        (case_id,),
    ).fetchall()
    con.close()
    qv = embed(query, allow_live=allow_live_embed)
    scored = []
    for r in rows:
        d = dict(r)
        emb = json.loads(d["embedding"]) if d["embedding"] else None
        d["score"] = _cosine(qv, emb) if (qv and emb) else 0.0
        d.pop("embedding", None)
        scored.append(d)
    if qv and any(s["score"] for s in scored):
        scored.sort(key=lambda s: -s["score"])
    else:
        scored.sort(key=lambda s: -s["created_at"])
    return scored[:k]
