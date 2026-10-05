"""Pull the real rows the three demo cases need out of the big source files and
write them as compact JSON into backend/data/.

Nothing here invents a number. Every value is copied from the files in
../../research/data (CMS public-domain CSVs, NJR OGL CSV, NOGCA CC-BY xlsx).
Where the source suppresses a cell (CMS <11 discharges), that absence is carried
through as a fact, not filled in. Run once; the app reads the JSON, so the
22 MB CMS file never has to ship in the container.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "research" / "data"
OUT = HERE / "data"
OUT.mkdir(exist_ok=True)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ── Case 1: Ohio pancreas/liver (DRG 405-407) + CMS safety measures ──────────
def us_pancreas_ohio():
    drg_file = SRC / "cms-medicare-inpatient-by-provider-drg-2024_DRG405-407_326-328_469-470.csv"
    volumes: dict[str, dict] = {}
    with open(drg_file, newline="") as f:
        for row in csv.DictReader(f):
            if row["Rndrng_Prvdr_State_Abrvtn"] != "OH":
                continue
            if row["DRG_Cd"] not in ("405", "406", "407"):
                continue
            ccn = row["Rndrng_Prvdr_CCN"]
            v = volumes.setdefault(ccn, {
                "ccn": ccn,
                "name": row["Rndrng_Prvdr_Org_Name"].title(),
                "city": row["Rndrng_Prvdr_City"].title(),
                "zip": row["Rndrng_Prvdr_Zip5"],
                "discharges": 0,
                "drg_cells": [],
            })
            n = int(float(row["Tot_Dschrgs"]))
            v["discharges"] += n
            v["drg_cells"].append({"drg": row["DRG_Cd"], "desc": row["DRG_Desc"], "n": n})

    # PSI_04 (failure to rescue) and PSI_90 (safety composite) per CCN
    comp_file = SRC / "cms-complications-and-deaths-hospital-2026-09-10.csv"
    wanted = set(volumes)
    psi: dict[str, dict] = {ccn: {} for ccn in wanted}
    with open(comp_file, newline="") as f:
        for row in csv.DictReader(f):
            ccn = row["Facility ID"]
            if ccn not in wanted:
                continue
            mid = row["Measure ID"]
            if mid in ("PSI_04", "PSI_90", "PSI_90_SAFETY"):
                key = "PSI_90" if mid.startswith("PSI_90") else "PSI_04"
                psi[ccn][key] = {
                    "score": _f(row["Score"]),
                    "compared": row["Compared to National"],
                    "denominator": row["Denominator"],
                    "lower": _f(row["Lower Estimate"]),
                    "higher": _f(row["Higher Estimate"]),
                    "footnote": row["Footnote"],
                }

    hospitals = []
    for ccn, v in sorted(volumes.items(), key=lambda kv: -kv[1]["discharges"]):
        v["psi"] = psi.get(ccn, {})
        hospitals.append(v)
    return hospitals


# ── Case 2: East Midlands joint replacement (NJR transparency) ───────────────
def uk_hip_eastmidlands():
    njr = SRC / "njr-transparency-Datagov2025.csv"
    # the trusts/providers around Nottingham used in the computed demo view
    keep = [
        "Nottingham City Hospital", "Queens Medical Centre Nottingham",
        "Nottingham Treatment Centre", "King's Mill Hospital", "Newark Hospital",
        "Royal Derby Hospital", "Queens Hospital Burton",
        "Leicester General Hospital", "Leicester Royal Infirmary",
        "Nuffield Health Derby", "Nuffield Health Leicester",
        "Nottingham Woodthorpe", "Spire Leicester", "Spire Nottingham",
        "Ilkeston Community Hospital",
    ]
    outlier_cols = {
        "Outliers - Hip 90-day mortality": "Hip 90-day mortality",
        "Outliers - Hip 5-year revision": "Hip 5-year revision",
        "Outliers - Hip 10-year revision": "Hip 10-year revision",
        "Outliers - Total Knee 5-year revision": "Total Knee 5-year revision",
        "Outliers - Total Knee 10-year revision": "Total Knee 10-year revision",
    }
    rows = []
    with open(njr, newline="") as f:
        for row in csv.DictReader(f):
            hosp = row["Hospital"].split("_", 1)[-1]
            if not any(k.lower() in hosp.lower() for k in keep):
                continue
            flags = [label for col, label in outlier_cols.items()
                     if (row.get(col) or "").strip().upper() == "Y"]
            rows.append({
                "trust": row["Trust/Company"],
                "hospital": hosp,
                "procedures": int(float(row["Number of procedures 2025"])),
                "consultants": int(float(row["Number of consultants 2025"])),
                "outliers": flags,
            })
    rows.sort(key=lambda r: -r["procedures"])
    return rows


# ── Case 3: England/Wales oesophago-gastric cancer surgery (NOGCA 2019-22) ───
def uk_og_england():
    import openpyxl  # local import; only needed here
    wb = openpyxl.load_workbook(SRC / "NOGCA_Report-2023_Data-tables_v2.0.xlsx",
                                data_only=True)
    ws = wb["9-OGC Curative surgery"]
    rows = []
    for r in ws.iter_rows(min_row=11, values_only=True):
        name = r[4]
        if not name or not isinstance(name, str):
            continue
        oeso, gastr, total, adj30, adj90 = r[5], r[6], r[7], r[8], r[9]
        if total in (None, ""):
            continue
        rows.append({
            "centre": name.strip(),
            "oesophagectomies": None if isinstance(oeso, str) else oeso,
            "gastrectomies": None if isinstance(gastr, str) else gastr,
            "total": None if isinstance(total, str) else total,
            "adj_30d_mortality": None if isinstance(adj30, str) else adj30,
            "adj_90d_mortality": None if isinstance(adj90, str) else adj90,
        })
    rows.sort(key=lambda r: -(r["total"] or 0))
    return rows


def main():
    datasets = {
        "us_pancreas_ohio": us_pancreas_ohio(),
        "uk_hip_eastmidlands": uk_hip_eastmidlands(),
        "uk_og_england": uk_og_england(),
    }
    for name, rows in datasets.items():
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(rows, indent=2))
        print(f"wrote {path.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
