"""Seed the three example cases, their persistent memory, and precompute the
assessment cache so the deployed demo costs a judge no tokens.

The hospital figures in every case are real public data. The patients and their
letters are illustrative examples written to exercise that data — they are never
presented as real people's records (see research GAPS). The point being
demonstrated is persistent memory: a case built up over several sessions, which
the agent recalls and acts on.
"""

from __future__ import annotations

import sys
import time

import agent
import memory

# ── the three example cases ──────────────────────────────────────────────────
CASES = [
    {
        "case": {
            "id": "ray-pancreas-oh",
            "label": "Raymond — Whipple for pancreatic cancer",
            "region": "US",
            "diagnosis": "Pancreatic adenocarcinoma, head of pancreas",
            "operation": "Whipple (pancreaticoduodenectomy)",
            "operation_key": "pancreatic resection",
            "dataset": "us_volume_safety",
            "surgeon": "named in the clinic letter",
            "hospital": "the community hospital near his home in Ohio",
            "network": "Anthem Blue Cross PPO (Ohio)",
            "travel_miles": 60,
            "consultation": "2026-10-20",
        },
        "letter": (
            "Dear Mr. ------,\n\nFollowing your CT and the MDT discussion, we recommend a "
            "pancreaticoduodenectomy (a 'Whipple' operation) for the tumour in the head of "
            "your pancreas. I propose to carry this out here at our local hospital. "
            "I perform a few of these each year. Please attend the pre-operative "
            "clinic on 20 October to discuss.\n\nYours sincerely,\nConsultant Surgeon"
        ),
        "memory": [
            ("patient", "message", "I got a letter saying I need a Whipple operation for "
             "pancreatic cancer. The surgeon wants to do it at my local hospital. "
             "He said he does 'a few a year'. Is that enough?"),
            ("patient", "answer", "I could drive about an hour if a bigger centre would be "
             "safer. I'm on Anthem Blue Cross."),
            ("agent", "action", "Mapped the operation to pancreatic resection and pulled "
             "Medicare FFS volume for pancreas/liver operations in Ohio plus CMS safety "
             "measures. The named hospital is not in the file."),
        ],
    },
    {
        "case": {
            "id": "margaret-hip-notts",
            "label": "Margaret's mum — hip replacement, Nottingham",
            "region": "UK",
            "diagnosis": "Osteoarthritis of the right hip",
            "operation": "Total hip replacement",
            "operation_key": "total hip replacement",
            "dataset": "uk_joint_registry",
            "surgeon": "to be assigned at the unit",
            "hospital": "Nottingham City Hospital",
            "network": "NHS — East Midlands",
            "travel_miles": 25,
            "consultation": "2026-11-03",
        },
        "letter": (
            "GP referral: Mrs ------'s right hip osteoarthritis has progressed and she now "
            "has constant pain and reduced mobility. I am referring her for assessment for a "
            "total hip replacement at Nottingham City Hospital under the orthopaedic team."
        ),
        "memory": [
            ("patient", "message", "A few weeks ago I asked you about Mum's knee pain and "
             "whether she should see someone."),
            ("agent", "answer", "We noted her symptoms and that a referral might follow."),
            ("patient", "message", "Now her GP has referred her to Nottingham City Hospital "
             "for a hip replacement. Is that a good place for it?"),
        ],
    },
    {
        "case": {
            "id": "og-cancer-england",
            "label": "Oesophagectomy for cancer — England",
            "region": "UK",
            "diagnosis": "Oesophageal cancer, stage 2, performance status 1",
            "operation": "Oesophagectomy",
            "operation_key": "esophagectomy",
            "dataset": "uk_og_surgery",
            "surgeon": "regional OG cancer centre team",
            "hospital": "regional oesophago-gastric cancer centre",
            "network": "NHS — curative pathway",
            "travel_miles": 50,
            "consultation": "2026-10-28",
        },
        "letter": (
            "The oesophago-gastric MDT has reviewed your case. Your cancer is considered "
            "potentially curable and we are recommending an oesophagectomy at the regional "
            "specialist centre. The team will discuss the plan, the risks, and your recovery "
            "with you at the clinic appointment."
        ),
        "memory": [
            ("patient", "message", "I've been told my oesophageal cancer might be curable "
             "with an operation. It's a big one. Should I try to get it done somewhere that "
             "does the most of them?"),
            ("patient", "answer", "I'm well enough for surgery and I just want the best "
             "chance. I can travel if it makes a real difference."),
        ],
    },
]


def main(live: bool = True):
    memory.init_db()
    for entry in CASES:
        case = entry["case"]
        memory.create_case(case)
        # seed persistent memory, spacing timestamps so the timeline reads in order
        for i, (role, kind, text) in enumerate(entry["memory"]):
            mid = memory.add_memory(case["id"], role, kind, text,
                                    allow_live_embed=live)
            # backdate a little so "across sessions" is visible
            con = memory.connect()
            con.execute("UPDATE memory SET created_at=? WHERE id=?",
                        (time.time() - (len(entry["memory"]) - i) * 86400, mid))
            con.commit(); con.close()
        print(f"[seed] case {case['id']}: memory seeded")
        # precompute the assessment (runs Nano/Lightning/Super/Ultra once, caches it)
        result = agent.assess_case(case, live=live, letter_text=entry["letter"])
        print(f"[seed]   assessment cached — verdict: "
              f"{result['judgment'].get('volume_verdict','')[:80]}")
    print("[seed] done")


if __name__ == "__main__":
    # `python seed.py offline` seeds structure without calling the model
    main(live="offline" not in sys.argv)
