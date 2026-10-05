"""The agent. Nemotron does every judgement; the numbers come from the real data.

Four tiers, each doing what it is best at (and cheapest at):
  Nano      — reads the letter and maps the operation to a procedure + dataset.
  Lightning — the tool-calling step: it chooses which real dataset to pull.
  Super     — drafts the plain-language reading of the comparison.
  Ultra     — the one hard call: does hospital volume decide for THIS operation,
              what can honestly be said, and what to ask the surgeon.

A model never emits a statistic. The data layer owns the numbers; the models read,
weigh and explain them, and are told in the system prompt never to invent figures,
never to name a safest hospital, and never to show Leapfrog results.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cases as caselaw
import data_sources
import evidence
import memory
from nemotron import LIGHTNING, NANO, SUPER, ULTRA, think

CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)

GROUND_RULES = (
    "You are Second Opinion, a surgical patient's own advocate. Ironclad rules: "
    "never invent a statistic — every number must come from the data you are given; "
    "never name a 'safest' or 'best' hospital or tell the patient where to have surgery; "
    "never present Leapfrog ratings; treat a missing or suppressed data cell as "
    "'unknown — ask', never as 'low'. You help the patient understand and ask better "
    "questions. Write plainly, for a frightened non-expert, in UK/US English as fits the case."
)

# which real dataset each case maps to (also what Nano is asked to produce)
DATASET_FOR = {
    "pancreatic resection": "us_volume_safety",
    "total hip replacement": "uk_joint_registry",
    "esophagectomy": "uk_og_surgery",
}


def map_operation(letter_text: str) -> dict:
    """Nano: read the patient's letter, map the operation to a procedure key and the
    dataset that applies. Cheap, low reasoning effort — this is classification."""
    sys = GROUND_RULES
    user = (
        "From this clinic letter, identify the operation and return STRICT JSON with keys: "
        '"operation" (the phrase used), "operation_key" (one of: "pancreatic resection", '
        '"total hip replacement", "esophagectomy"), "region" ("US" or "UK"), '
        '"dataset" (one of: "us_volume_safety", "uk_joint_registry", "uk_og_surgery"), '
        '"hospital" (the hospital named, or null), "rationale" (one sentence).\n\n'
        f"LETTER:\n{letter_text}"
    )
    out = think([{"role": "system", "content": sys}, {"role": "user", "content": user}],
                model=NANO, reasoning_effort="low", max_tokens=1200, json_out=True)
    return out


# Lightning tool-calling: the model chooses which dataset to open.
_TOOL_SCHEMA = [{
    "type": "function",
    "function": {
        "name": "open_dataset",
        "description": ("Open the real public dataset that bears on this operation and "
                        "region, returning the per-hospital comparison rows and the caveat."),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "enum": ["us_volume_safety", "uk_joint_registry", "uk_og_surgery"],
                    "description": "Which dataset to open.",
                },
            },
            "required": ["name"],
        },
    },
}]


def choose_dataset(operation: str, region: str) -> tuple[str, dict]:
    """Lightning decides which dataset tool to call; we execute it for real."""
    msgs = [
        {"role": "system", "content": GROUND_RULES},
        {"role": "user", "content": (
            f"The patient faces a {operation} in the {region}. Call open_dataset for the "
            "one dataset that applies: us_volume_safety for US pancreas/liver volume+safety, "
            "uk_joint_registry for UK hip/knee replacement, uk_og_surgery for UK "
            "oesophago-gastric cancer surgery.")},
    ]
    msg = think(msgs, model=LIGHTNING, tools=_TOOL_SCHEMA, max_tokens=800)
    name = None
    if getattr(msg, "tool_calls", None):
        try:
            name = json.loads(msg.tool_calls[0].function.arguments).get("name")
        except (json.JSONDecodeError, AttributeError):
            name = None
    expected = DATASET_FOR.get(operation)
    if name not in data_sources.TOOLS or (expected and name != expected):
        name = expected or "us_volume_safety"  # the mapping is authoritative
    return name, data_sources.run_tool(name)


def _rows_as_text(view: dict) -> str:
    lines = [view["title"], f"{len(view['rows'])} rows in total", "columns: " + ", ".join(c["label"] for c in view["columns"])]
    for r in view["rows"]:
        lines.append(" | ".join(f"{c['label']}={r.get(c['k'])}" for c in view["columns"]))
    lines.append("SOURCE: " + view["source"])
    lines.append("CAVEAT: " + view["caveat"])
    return "\n".join(lines)


def draft_reading(operation: str, view: dict, recalled: list[dict]) -> str:
    """Super: the plain-language reading of the comparison, honouring the caveat."""
    hist = "\n".join(f"- ({m['kind']}) {m['text']}" for m in recalled) or "(none yet)"
    user = (
        f"Operation: {operation}. Here is the real comparison from public data:\n\n"
        f"{_rows_as_text(view)}\n\n"
        f"Relevant memory from this patient's case:\n{hist}\n\n"
        "Write at most 110 words for the patient reading this table. Refer only to hospitals "
        "that are rows in the table, and use only the rows given; the patient's own hospital "
        "is not a row unless named there. Describe what the numbers show, point out where the data cannot tell them something, and respect the "
        "caveat exactly. Do not rank hospitals or name a safest one. Do not add any number "
        "that is not above."
    )
    msg = think([{"role": "system", "content": GROUND_RULES},
                 {"role": "user", "content": user}],
                model=SUPER, reasoning_effort="low", max_tokens=1600)
    return (msg.content or "").strip()


def final_judgment(operation: str, operation_key: str, view: dict) -> dict:
    """Ultra: the hard call — does volume decide here, and what should the patient do/ask."""
    studies = evidence.studies_for(operation_key)
    ev = "\n".join(f"- {s['cite']} (PMID {s.get('pmid','n/a')}): {s['finding']}"
                   for s in studies)
    weight = evidence.VOLUME_WEIGHT.get(operation_key, ("unknown", ""))
    stance = evidence.STANCE.get(operation_key, "")
    ev = ev or "(no volume-outcome studies apply; rely on the registry data below)"
    user = (
        f"Operation: {operation} (key: {operation_key}).\n"
        f"Evidence on whether hospital volume predicts death for THIS operation:\n{ev}\n\n"
        f"Settled position (explain and qualify it; never contradict it): {stance}\n\n"
        f"The real comparison the patient is looking at:\n{_rows_as_text(view)}\n\n"
        "Decide, grounded ONLY in the evidence above, and return STRICT JSON with keys:\n"
        '"volume_verdict": one short sentence stating how much hospital volume matters for '
        "THIS operation specifically (e.g. a lot / mixed / it is not the signal here);\n"
        '"explanation": 2-3 sentences of why, citing only studies listed above by author-year, each for what it actually found;\n'
        '"do_not": array of 2-3 things the patient should NOT conclude from this data;\n'
        '"next_step": one sentence on what the patient should actually do now.\n'
        "Remember: never name a safest hospital; honour that volume is a weak proxy."
    )
    out = think([{"role": "system", "content": GROUND_RULES},
                 {"role": "user", "content": user}],
                model=ULTRA, reasoning_effort="high", max_tokens=3000, json_out=True)
    out["volume_weight"] = weight[0]
    return out


def assess_case(case: dict, *, live: bool = False, letter_text: str | None = None) -> dict:
    """The full flow for one case. Cached to disk; `live=True` recomputes and re-caches."""
    cache_file = CACHE / f"assessment_{case['id']}.json"
    if not live and cache_file.exists():
        return json.loads(cache_file.read_text())

    operation = case.get("operation") or case.get("operation_key") or ""
    operation_key = case.get("operation_key") or ""
    region = case.get("region") or "US"
    mapping = {"operation": operation, "operation_key": operation_key,
               "region": region, "dataset": case.get("dataset"),
               "rationale": "mapped from the patient's case file"}

    # Stage 1 — Nano re-reads the letter if we have one (shows the mapping live)
    if letter_text:
        try:
            mapping = map_operation(letter_text)
            operation = mapping.get("operation", operation)
            operation_key = mapping.get("operation_key", operation_key)
            region = mapping.get("region", region)
        except Exception as e:  # noqa: BLE001 — never fail the whole flow on the cheap step
            mapping["rationale"] = f"mapping fell back to the case file ({type(e).__name__})"

    # Stage 2 — Lightning picks the dataset; we run it for real
    _, view = choose_dataset(operation_key or operation, region)

    # recall relevant memory (Personal AI: the agent uses what it already knows)
    recalled = memory.recall(case["id"], f"{operation} hospital volume safety",
                             k=4, allow_live_embed=live)

    # Stage 3 — Super reads; Stage 4 — Ultra judges
    reading = draft_reading(operation, view, recalled)
    judgment = final_judgment(operation, operation_key, view)

    result = {
        "case_id": case["id"],
        "generated_at": time.time(),
        "live": live,
        "mapping": mapping,
        "data": view,
        "reading": reading,
        "judgment": judgment,
        "questions": caselaw.SURGEON_QUESTIONS,
        "evidence": [
            {"cite": s["cite"], "pmid": s.get("pmid"), "finding": s["finding"],
             "counter": s.get("counter", False)}
            for s in evidence.studies_for(operation_key)
        ],
        "cases_cited": [
            {"name": c["name"], "citation": c["citation"], "court": c["court"],
             "year": c["year"], "why": c["why"], "url": c["url"]}
            for c in caselaw.CASES
            if (region == "UK") == (c.get("jurisdiction") == "UK") or c["id"] == "johnson-v-kokemoor"
        ],
        "models": {
            "map": NANO, "tool": LIGHTNING, "reading": SUPER, "judgment": ULTRA,
        },
    }
    cache_file.write_text(json.dumps(result, indent=2))

    # record what the agent did, into persistent memory (so it compounds across sessions)
    memory.add_memory(
        case["id"], "agent", "finding",
        f"Assessed {operation}: {judgment.get('volume_verdict','')} "
        f"Read {view['title']}.",
        allow_live_embed=live,
    )
    return result


def reply_to(case: dict, text: str, *, live: bool = True) -> str:
    """Super answers a new patient message from the case file and recalled memory."""
    recalled = memory.recall(case["id"], text, k=5, allow_live_embed=live)
    hist = "\n".join(f"- ({m['role']}/{m['kind']}) {m['text']}" for m in recalled)
    cache_file = CACHE / f"assessment_{case['id']}.json"
    verdict = ""
    if cache_file.exists():
        verdict = json.loads(cache_file.read_text())["judgment"].get("volume_verdict", "")
    file_ = (f"Operation: {case.get('operation')}. Hospital: {case.get('hospital')}. "
             f"Network: {case.get('network')}. Will travel: {case.get('travel_miles')} miles. "
             f"Next appointment: {case.get('consultation')}. Earlier finding: {verdict}")
    user = (f"Case file: {file_}\n\nRelevant earlier memory:\n{hist}\n\n"
            f"New message from the patient: {text}\n\n"
            "Reply in at most 70 words. Use what you remember. If they report something the "
            "surgeon said, say what it changes and what to ask next. No new statistics.")
    msg = think([{"role": "system", "content": GROUND_RULES},
                 {"role": "user", "content": user}],
                model=SUPER, reasoning_effort="low", max_tokens=1200)
    return (msg.content or "").strip()
