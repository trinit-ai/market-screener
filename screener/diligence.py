"""Stage 2 checklist. The bot produces the number; these decide whether the
discount is justified. Several of these deliberately cannot be automated.
"""
CHECKLIST = [
    ("county_tax",     "AUTO", "Pull the actual county effective rate. State medians hide enormous variance — Dayton is 2.04% against Ohio's 1.36% median. Verify reassessment-on-sale rules."),
    ("insurance_quote","AUTO", "Get a real landlord DP-3 quote at the target value. State averages are HO-3 owner-occupied and understate landlord cost by 15-25%."),
    ("population",     "AUTO", "Census ACS 5yr population trend. Declining population impairs your exit even when current yield looks fine."),
    ("employers",      "AUTO", "BLS QCEW employment by sector. One employer above ~15% of jobs is single-point-of-failure risk."),
    ("rent_comps",     "AUTO", "Three actual rent comps within a mile of a candidate property. Bedroom-count metro averages are not comps."),
    ("eviction_law",   "MANUAL","Read the county's actual timeline. Statewide 'landlord friendly' ratings miss county courts that run six months."),
    ("pm_availability","MANUAL","THE remote-landlording gate. Find 3+ managers with 100+ doors and verifiable reviews. No PM industry means the market is untouchable from a distance, whatever the math says."),
    ("boots_on_ground","MANUAL","One trip, or one trusted local. Nothing in this repo distinguishes a street that is stable from one that is emptying."),
    ("crime_schools",  "MANUAL","Block-level. Zip-level data is too coarse to be useful in exactly the markets that screen best."),
]

def print_checklist(market: str) -> None:
    print(f"\nStage-2 diligence — {market}\n" + "=" * (22 + len(market)))
    for key, mode, why in CHECKLIST:
        print(f"  [{mode:6}] {key:17} {why}")
    print("\n  A market cannot clear Stage 2 on AUTO checks alone. The MANUAL items")
    print("  are where 'cheap because boring' separates from 'cheap because broken'.")
