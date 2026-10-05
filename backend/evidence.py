"""The verified evidence base. Every figure here is copied from a saved abstract
(research/evidence/pubmed-*.txt) and summarised in research/evidence/EVIDENCE-LOG.md.
No figure is invented; counter-evidence sits beside the headline on purpose, because
the product's whole claim is that it tells you when volume does NOT decide.

Leapfrog results are never shown (their terms forbid republication). Only the
published volume thresholds appear — they are also printed in the peer-reviewed
papers below — plus a pointer to look a hospital up on Leapfrog's own site.
"""

# Volume-outcome evidence, by procedure, so the agent can say where volume weighs
# heavily and where it barely does.
STUDIES = [
    {
        "id": "kalata-2024",
        "cite": "Kalata et al., JAMA Surgery 2024;159(2):203-210",
        "pmid": "38150228",
        "headline": True,
        "finding": ("30-day mortality was 8.1% at low-volume hospitals versus 5.5% "
                    "at hospitals meeting the volume standard (adjusted odds ratio 0.67). "
                    "For 79.8% of operations done at a low-volume hospital, a hospital "
                    "meeting the standard sat in the same insurance network, a median of "
                    "29 miles from the patient's home."),
        "base": "1,049,069 elective high-risk operations, Medicare 2016-2018, 2,469 hospitals.",
        "procedures": ["pancreatic resection", "esophagectomy", "lung resection",
                       "rectal cancer surgery", "carotid endarterectomy"],
        "note": ("Low-volume surgery ranged from 1.5% of carotid endarterectomies to "
                 "65.0% of esophagectomies — the stakes of going low-volume are not the "
                 "same operation to operation."),
    },
    {
        "id": "sheetz-2019",
        "cite": "Sheetz et al., JAMA Surgery 2019;154(11):1005-1012",
        "pmid": "31411663",
        "finding": ("For pancreatic resection, risk-adjusted mortality was 3.8% at "
                    "hospitals meeting the Leapfrog standard versus 5.7% at those not. "
                    "There was no significant difference for esophageal, lung or rectal "
                    "resection."),
        "base": "516,392 Medicare cancer resections, 2005-2016.",
        "procedures": ["pancreatic resection"],
        "weighs": {"pancreatic resection": "high", "esophagectomy": "low",
                   "lung resection": "low", "rectal cancer surgery": "low"},
    },
    {
        "id": "sheetz-centralization-2019",
        "cite": "Sheetz, Dimick, Nathan, J Clin Oncol 2019;37(34):3234-3242",
        "pmid": "31251691",
        "finding": ("Within hospital systems, pancreatectomy 30-day mortality was 8.9% "
                    "in the least centralised systems versus 3.7% in the most centralised "
                    "— independent of volume. No benefit for colectomy or proctectomy."),
        "procedures": ["pancreatic resection"],
    },
    {
        "id": "cancer-2021",
        "cite": "Cancer 2021;127(21):4059-4071",
        "pmid": "34292582",
        "finding": ("Even among surgeons who met the volume standard, 90-day "
                    "esophagectomy mortality ranged from 3.5% to 9.3%. Meeting a volume "
                    "bar is not the same as a good outcome."),
        "procedures": ["esophagectomy"],
    },
    # counter-evidence — load-bearing, must stay beside the headline
    {
        "id": "wasif-2020",
        "cite": "Wasif et al., J Am Coll Surg 2020;231(1):45-52",
        "pmid": "32335321",
        "counter": True,
        "procedures": ["pancreatic resection", "esophagectomy", "lung resection",
                       "rectal cancer surgery", "carotid endarterectomy"],
        "finding": ("Leapfrog volume thresholds had a positive predictive value of only "
                    "24-26% for identifying poor-performing hospitals. Case-volume cut-offs "
                    "alone do not track actual hospital mortality well."),
    },
    {
        "id": "madenci-2022",
        "cite": "Madenci et al., JAMA Network Open 2022;5(3):e221766",
        "pmid": "35267034",
        "counter": True,
        "procedures": ["pancreatic resection"],
        "finding": ("For pancreatectomy, a naive lower-vs-higher-volume mortality gap of "
                    "7.9% vs 5.2% shrank to 7.8% vs 7.2% once the comparison was defined "
                    "cleanly — much of the raw volume effect was bias."),
    },
    # UK centralisation
    {
        "id": "nogca-2026",
        "cite": "National Oesophago-Gastric Cancer Audit, State of the Nation 2026 (HQIP)",
        "finding": ("After England centralised oesophago-gastric cancer surgery, 90-day "
                    "survival after curative surgery was 96.7% and no surgical centre was "
                    "a 90-day mortality outlier. But length of stay over 15 days ranged "
                    "11%-40% between centres and 30-day readmission ranged 7%-29%; and only "
                    "67% of fit stage 1-3 patients started curative treatment. The audit "
                    "says a second-opinion review 'may be beneficial' in borderline cases."),
        "procedures": ["esophagectomy", "gastrectomy"],
        "weighs": {"esophagectomy": "low-for-death", "gastrectomy": "low-for-death"},
    },
    {
        "id": "hpb-2018",
        "cite": "HPB 2018;20(11):1012-1020",
        "pmid": "29895441",
        "finding": ("UK pancreatoduodenectomy 90-day mortality fell from 10.0% (2001-04) "
                    "to 4.1% (2013-16) after centralisation, with no difference between "
                    "high and very-high volume centres once centralised."),
        "procedures": ["pancreatic resection"],
    },
    {
        "id": "bmj-2023-shoulder",
        "cite": "BMJ 2023;381:e075355",
        "pmid": "37343999",
        "finding": ("For shoulder replacement, below about 10.4 procedures per surgeon per "
                    "year revision risk rose up to roughly double (HR 1.94)."),
        "procedures": ["shoulder replacement"],
    },
]

# Published Leapfrog minimum annual volumes (hospital / surgeon). These thresholds
# are printed in the peer-reviewed papers above and in Leapfrog's public survey, so
# stating them is fine; Leapfrog's hospital *results* are not shown.
LEAPFROG_THRESHOLDS = {
    "pancreatic resection": {"hospital": 20, "surgeon": 10},
    "esophagectomy": {"hospital": 20, "surgeon": 7},
    "lung resection": {"hospital": 40, "surgeon": 15},
    "rectal cancer surgery": {"hospital": 16, "surgeon": 6},
    "carotid endarterectomy": {"hospital": 20, "surgeon": 10},
    "mitral valve surgery": {"hospital": 40, "surgeon": 20},
    "open aortic surgery": {"hospital": 10, "surgeon": 7},
    "bariatric surgery": {"hospital": 50, "surgeon": 20},
    "total knee replacement": {"hospital": 50, "surgeon": 25},
    "total hip replacement": {"hospital": 50, "surgeon": 25},
}

# How much hospital volume weighs on 30/90-day death, per operation, from the
# evidence above. This is the judgement the agent must get right; it is grounded,
# not a guess.
VOLUME_WEIGHT = {
    "pancreatic resection": ("high", "sheetz-2019", "kalata-2024"),
    "esophagectomy": ("mixed", "kalata-2024", "cancer-2021"),
    "carotid endarterectomy": ("low", "kalata-2024"),
    "lung resection": ("low", "sheetz-2019"),
    "rectal cancer surgery": ("low", "sheetz-2019"),
    "total hip replacement": ("volume-not-the-signal", "njr"),
    "total knee replacement": ("volume-not-the-signal", "njr"),
}


def studies_for(procedure: str) -> list[dict]:
    """Every study that names this procedure, headline and counter together."""
    out = [s for s in STUDIES if procedure in s.get("procedures", [])]
    # de-dup preserving order
    seen, keep = set(), []
    for s in out:
        if s["id"] not in seen:
            seen.add(s["id"]); keep.append(s)
    return keep


# What the evidence supports saying, per operation. The judgment model must not
# contradict this; it explains and qualifies it.
STANCE = {
    "pancreatic resection": ("Of the operations studied, pancreatic resection is where hospital "
        "volume shows the clearest link to death (Sheetz 2019: 3.8% vs 5.7%; Kalata 2024's 8.1% vs 5.5% pools five operations). "
        "Caveats stand: volume is a weak proxy (Wasif 2020) and part of the raw gap was "
        "bias (Madenci 2022)."),
    "esophagectomy": ("In the US low-volume surgery is common for esophagectomy (65.0%) but "
        "Sheetz 2019 found no significant mortality difference by volume, and surgeon results "
        "vary widely even above the bar. In England, centralisation means no centre is a "
        "90-day mortality outlier; readmission and stay vary instead."),
    "total hip replacement": ("Volume is not the signal here. The registry flags are for "
        "revision years later, not death; no unit is a hip 90-day mortality outlier."),
}
