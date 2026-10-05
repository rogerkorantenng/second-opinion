"""The four verified court cases. Holdings are quoted or closely paraphrased from
the opinions saved in research/court-cases/ (CourtListener + supremecourt.uk).
No award amounts appear in any of these opinions, so none are stated here.

They are in the product because a court has said the three things Second Opinion
helps a patient weigh — how many has this surgeon done, how do the outcomes
compare, is there a better-equipped centre within reach — are material to consent.
US law is split by state, which is exactly why the patient has to ask.
"""

CASES = [
    {
        "id": "johnson-v-kokemoor",
        "name": "Johnson ex rel. Adler v. Kokemoor",
        "court": "Supreme Court of Wisconsin",
        "year": 1996,
        "citation": "199 Wis. 2d 615, 545 N.W.2d 495",
        "url": "https://www.courtlistener.com/opinion/1691094/johnson-ex-rel-adler-v-kokemoor/",
        "on_point": True,
        "facts": ("Asked how many basilar bifurcation aneurysm operations he had done, "
                  "the surgeon said 'dozens'. He had done two, and never one this large. "
                  "He quoted a 2% risk; the plaintiff's experts put it at 20-30% for a "
                  "surgeon of his experience. She was left an incomplete quadriplegic. "
                  "Experts said she should have been referred to a tertiary centre 'such "
                  "as the Mayo Clinic, only 90 miles away'."),
        "held": ("The surgeon's limited experience, the comparative morbidity and "
                 "mortality of experienced versus inexperienced surgeons, and the "
                 "availability of a more experienced centre nearby were all material to "
                 "informed consent and properly before the jury."),
        "why": ("A court named the exact three questions this agent helps a patient ask "
                "— and called them material to consent."),
    },
    {
        "id": "andersen-v-khanna",
        "name": "Andersen v. Khanna and Iowa Heart Center",
        "court": "Supreme Court of Iowa",
        "year": 2018,
        "citation": "913 N.W.2d 526",
        "url": "https://www.courtlistener.com/opinion/4507580/alan-andersen-v-sohit-khanna-and-iowa-heart-center/",
        "facts": ("The surgeon had no experience or training in the particular Bentall "
                  "procedure used. Complications led to a coma, a second heart operation "
                  "and a heart transplant."),
        "held": ("Whether a physician's training and experience with a particular "
                 "procedure is material depends on the facts; it was wrong to rule as a "
                 "matter of law that there is no duty to disclose inexperience. The "
                 "informed-consent claims were remanded. The court cited Johnson v. "
                 "Kokemoor approvingly."),
        "why": "Confirms, 22 years later, that a surgeon's inexperience can be material.",
    },
    {
        "id": "howard-v-umdnj",
        "name": "Howard v. University of Medicine & Dentistry of New Jersey",
        "court": "Supreme Court of New Jersey",
        "year": 2002,
        "citation": "172 N.J. 537, 800 A.2d 73",
        "url": "https://www.courtlistener.com/opinion/1473677/howard-v-university-of-medicine-dentistry/",
        "facts": ("The patient was told the surgeon was board certified and had done about "
                  "sixty corpectomies a year for eleven years; at deposition he said he was "
                  "not then board certified and had done 'a couple dozen' in his career."),
        "held": ("A serious misrepresentation about the quality or extent of a physician's "
                 "experience can be material to informed consent, subject to a two-step "
                 "causation test — though it does not amount to a separate fraud claim."),
        "why": "Misstated experience is a consent problem, not just a bedside-manner one.",
    },
    {
        "id": "montgomery-v-lanarkshire",
        "name": "Montgomery v Lanarkshire Health Board",
        "court": "UK Supreme Court",
        "year": 2015,
        "citation": "[2015] UKSC 11",
        "url": "https://www.supremecourt.uk/cases/uksc-2013-0136",
        "jurisdiction": "UK",
        "facts": ("A diabetic mother was not told of the 9-10% shoulder-dystocia risk of "
                  "vaginal delivery; the baby was born with serious disabilities. The facts "
                  "are obstetric — the case is used only for the UK consent standard."),
        "held": ("A doctor must take reasonable care to ensure the patient is aware of any "
                 "material risks and of any reasonable alternative or variant treatments, "
                 "judged by what a reasonable person in the patient's position would be "
                 "likely to attach significance to (para 87)."),
        "why": ("The UK standard: reasonable alternatives — which can include a different "
                "unit — are part of what a patient is entitled to weigh."),
    },
]

# The three questions Johnson v. Kokemoor effectively endorsed, reused by the agent
# whenever the public data cannot settle the matter (suppressed cells, no outcome data).
SURGEON_QUESTIONS = [
    "How many of these operations have you personally done, and how many in the last year?",
    "How do your own results — mortality, serious complications — compare with other centres?",
    "Is there a hospital nearby that does more of these, and would you refer me there?",
]


def cases_by_id():
    return {c["id"]: c for c in CASES}
