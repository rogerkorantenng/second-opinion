"""The real datasets, shaped into the comparison a patient actually faces.

These are the agent's tools: each returns real rows from the extracted JSON, with
the source line and — this is the point — the caveat that keeps the numbers honest.
Absence is carried through as 'unknown, ask', never as 'low'. No row is invented.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def _load(name: str) -> list[dict]:
    return json.loads((DATA / f"{name}.json").read_text())


def us_volume_safety(state: str = "OH") -> dict:
    """US: Medicare FFS discharge volume for pancreas/liver operations (DRG 405-407)
    joined to the two CMS surgical-safety measures. The honest reading is built in."""
    rows = _load("us_pancreas_ohio")
    out = []
    for h in rows:
        psi04 = h["psi"].get("PSI_04", {})
        psi90 = h["psi"].get("PSI_90", {})
        out.append({
            "hospital": h["name"],
            "city": h["city"],
            "volume_2024": h["discharges"],
            "psi04_compared": psi04.get("compared") or "Not available",
            "psi90_score": psi90.get("score"),
            "psi90_compared": psi90.get("compared") or "Not available",
        })
    return {
        "key": "us_volume_safety",
        "region": "US",
        "title": "Pancreas & liver operations, Medicare fee-for-service 2024, with CMS safety measures — Ohio",
        "columns": [
            {"k": "hospital", "label": "Hospital"},
            {"k": "city", "label": "City"},
            {"k": "volume_2024", "label": "Medicare FFS volume (DRG 405-407)", "num": True},
            {"k": "psi04_compared", "label": "Failure-to-rescue (PSI-04) vs national"},
            {"k": "psi90_compared", "label": "Safety composite (PSI-90) vs national"},
        ],
        "rows": out,
        "source": ("Medicare Inpatient by Provider & DRG 2024; CMS Complications & Deaths — "
                   "Hospital, Sep 2026 (both US government, public domain)."),
        "caveat": ("Only hospitals with 11 or more Medicare fee-for-service cases appear. A "
                   "hospital that is absent did fewer than 11 such cases in 2024, or none — "
                   "that is 'unknown, ask the surgeon', not proof of low volume. DRG 405-407 "
                   "also mixes pancreas with liver and shunt procedures, so the count is a "
                   "proxy. Notice the highest-volume hospital here is the one flagged 'worse "
                   "than national' on the safety composite: volume and safety can disagree."),
    }


def uk_joint_registry() -> dict:
    """UK: National Joint Registry transparency data for the East Midlands."""
    rows = _load("uk_hip_eastmidlands")
    out = [{
        "hospital": r["hospital"],
        "procedures_2025": r["procedures"],
        "consultants": r["consultants"],
        "outliers": ", ".join(r["outliers"]) if r["outliers"] else "none",
    } for r in rows]
    return {
        "key": "uk_joint_registry",
        "region": "UK",
        "title": "Hip & knee replacement — National Joint Registry transparency data, 2025 (East Midlands)",
        "columns": [
            {"k": "hospital", "label": "Hospital"},
            {"k": "procedures_2025", "label": "Procedures 2025", "num": True},
            {"k": "consultants", "label": "Consultants", "num": True},
            {"k": "outliers", "label": "Outlier flags"},
        ],
        "rows": out,
        "source": "National Joint Registry Annual Report 2026 transparency data (Open Government Licence).",
        "caveat": ("No hospital in England is an outlier for hip 90-day mortality. The flags "
                   "here are for revision rates years later, not for dying — and the flagged "
                   "unit is one of the busiest. High volume is not the same as safe, and a "
                   "revision outlier is not a mortality outlier."),
    }


def uk_og_surgery() -> dict:
    """UK: NOGCA centre-level oesophago-gastric cancer surgery, 2019-22."""
    rows = _load("uk_og_england")
    out = []
    for r in rows:
        def pct(v):
            return None if v is None else round(v * 100, 1)
        out.append({
            "centre": r["centre"],
            "oesophagectomies": r["oesophagectomies"],
            "gastrectomies": r["gastrectomies"],
            "total": r["total"],
            "adj_30d_pct": pct(r["adj_30d_mortality"]),
            "adj_90d_pct": pct(r["adj_90d_mortality"]),
        })
    return {
        "key": "uk_og_surgery",
        "region": "UK",
        "title": "Oesophago-gastric cancer surgery by centre — NOGCA 2019-22 (England & Wales)",
        "columns": [
            {"k": "centre", "label": "Surgical centre"},
            {"k": "total", "label": "Total cases", "num": True},
            {"k": "adj_30d_pct", "label": "Adj. 30-day mortality %", "num": True},
            {"k": "adj_90d_pct", "label": "Adj. 90-day mortality %", "num": True},
        ],
        "rows": out,
        "source": "National Oesophago-Gastric Cancer Audit 2023 data tables, 2019-22 (CC BY, HQIP).",
        "caveat": ("The audit's own finding: every centre was within the expected range for "
                   "90-day mortality (one was outside for 30-day). The spread you see in the "
                   "raw percentages is within statistical noise — so this is not a league "
                   "table. In a centralised system the question shifts from 'will I die here' "
                   "to readmission, length of stay, and whether curative surgery is offered "
                   "at all."),
    }


TOOLS = {
    "us_volume_safety": us_volume_safety,
    "uk_joint_registry": uk_joint_registry,
    "uk_og_surgery": uk_og_surgery,
}


def run_tool(name: str, **kwargs) -> dict:
    fn = TOOLS.get(name)
    if not fn:
        return {"error": f"no such dataset tool: {name}"}
    return fn(**kwargs)
