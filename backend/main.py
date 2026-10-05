"""Second Opinion API + static frontend on one port."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import memory

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"

app = FastAPI(title="Second Opinion")

# Live model calls are capped per process so a public URL cannot drain the credit.
LIVE_BUDGET = 60
_live_used = 0
_lock = threading.Lock()


def spend() -> None:
    global _live_used
    with _lock:
        if _live_used >= LIVE_BUDGET:
            raise HTTPException(429, "Live limit reached for this demo.")
        _live_used += 1


def bootstrap() -> None:
    memory.init_db()
    if memory.list_cases():
        return
    import seed
    seed.main(live=False)
    for c in memory.list_cases():
        f = agent.CACHE / f"assessment_{c['id']}.json"
        if f.exists():
            j = json.loads(f.read_text())
            memory.add_memory(
                c["id"], "agent", "finding",
                f"Assessed {c['operation']}: {j['judgment'].get('volume_verdict', '')} "
                f"Read {j['data']['title']}.", allow_live_embed=False)


bootstrap()


def _case(cid: str) -> dict:
    c = memory.get_case(cid)
    if not c:
        raise HTTPException(404, "No such case")
    return c


@app.get("/api/cases")
def cases():
    return [{k: c[k] for k in ("id", "label", "region", "operation", "consultation")}
            for c in memory.list_cases()]


@app.get("/api/cases/{cid}")
def case_detail(cid: str):
    c = _case(cid)
    f = agent.CACHE / f"assessment_{cid}.json"
    return {"case": c, "timeline": memory.timeline(cid),
            "assessment": json.loads(f.read_text()) if f.exists() else None}


class Msg(BaseModel):
    text: str


@app.post("/api/cases/{cid}/message")
def message(cid: str, body: Msg):
    c = _case(cid)
    text = body.text.strip()[:1500]
    if not text:
        raise HTTPException(400, "Empty message")
    spend()
    memory.add_memory(cid, "patient", "message", text)
    try:
        reply = agent.reply_to(c, text)
    except Exception:  # noqa: BLE001 - the message is saved either way
        reply = "I saved that to your case. I could not draft a reply just now."
    memory.add_memory(cid, "agent", "message", reply)
    return {"timeline": memory.timeline(cid)}


@app.get("/api/cases/{cid}/recall")
def recall(cid: str, q: str):
    _case(cid)
    spend()
    return memory.recall(cid, q, k=4)


@app.post("/api/cases/{cid}/run")
def run(cid: str):
    c = _case(cid)
    spend()
    f = agent.CACHE / f"assessment_{cid}.json"
    letter = None
    try:
        import seed
        letter = next((e["letter"] for e in seed.CASES if e["case"]["id"] == cid), None)
    except Exception:  # noqa: BLE001
        pass
    try:
        agent.assess_case(c, live=True, letter_text=letter)
    except SystemExit as e:
        raise HTTPException(503, str(e))
    return case_detail(cid)


@app.get("/api/health")
def health():
    return {"ok": True, "live_used": _live_used}


if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = STATIC / path
        return FileResponse(f if path and f.is_file() else STATIC / "index.html")
