"""Inter-rater agreement between two human label files.

Run this BEFORE trusting your ground truth: if humans don't agree, no AutoRater can.
Usage: python3 compare_raters.py data/golden.jsonl data/rater2.jsonl
"""
import json
import sys

from autorater.metrics import accuracy, cohen_kappa, weighted_kappa


def load(p):
    with open(p) as f:
        return {d["id"]: d for d in map(json.loads, filter(str.strip, f))}


a, b = load(sys.argv[1]), load(sys.argv[2])
ids = sorted(set(a) & set(b))
la = {i: a[i]["human"] for i in ids}
lb = {i: b[i]["human"] for i in ids}

ga, gb = [la[i]["grounded"] for i in ids], [lb[i]["grounded"] for i in ids]
ha, hb = [la[i]["helpful"] for i in ids], [lb[i]["helpful"] for i in ids]
fa, fb = [la[i]["failure"] for i in ids], [lb[i]["failure"] for i in ids]

print(f"Items in both files: {len(ids)}\n")
print(f"Grounded:  agree {accuracy(ga, gb):.0%}   kappa {cohen_kappa(ga, gb):.2f}")
print(f"Helpful:   exact {accuracy(ha, hb):.0%}   within 1 "
      f"{sum(abs(x - y) <= 1 for x, y in zip(ha, hb)) / len(ids):.0%}   weighted kappa {weighted_kappa(ha, hb):.2f}")
print(f"Failure:   agree {accuracy(fa, fb):.0%}   kappa {cohen_kappa(fa, fb):.2f}\n")

rows = [i for i in ids if la[i]["grounded"] != lb[i]["grounded"]
        or abs(la[i]["helpful"] - lb[i]["helpful"]) > 1 or la[i]["failure"] != lb[i]["failure"]]
if rows:
    print("Disagreements to settle (rater A vs rater B: grounded/helpful/failure):\n")
    for i in rows:
        resp = (a[i].get("response") or b[i].get("response") or "")[:80]
        print(f"  {i}: A {la[i]['grounded']}/{la[i]['helpful']}/{la[i]['failure']}"
              f"   B {lb[i]['grounded']}/{lb[i]['helpful']}/{lb[i]['failure']}")
        print(f"      \"{resp}\"")
        for who, lab in (("A", la[i]), ("B", lb[i])):
            if lab.get("note"):
                print(f"      {who} note: {lab['note']}")
print("\nTarget: grounded kappa >= 0.8 before calibrating an AutoRater against this set.")
