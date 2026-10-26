"""Settle disagreements between two raters, one item at a time.

For each item where the raters differ, it shows the item and both labels, and you choose:
  a = keep rater A's label     b = take rater B's label
  n = enter a new label        s = skip for now
You can also write a ruling, which is logged to docs/RULINGS_LOG.md for the labeling guide.

Usage:
  python3 settle.py data/golden.jsonl data/rater2.jsonl
  python3 settle.py data/golden.jsonl data/rater2.jsonl --out data/golden_settled.jsonl

By default it updates the first file in place, after saving a backup (<file>.bak).
"""
import argparse
import json
import os
import shutil
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
FAILURES = ["none", "contradiction", "fabricated_fact", "unsupported_claim", "policy_violation", "evasive"]


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def ask(prompt, valid):
    while True:
        v = input(prompt).strip().lower()
        if v in valid:
            return v
        print(f"  Please enter one of: {', '.join(valid)}")


def differs(x, y):
    return (x["grounded"] != y["grounded"] or x["failure"] != y["failure"]
            or abs(x["helpful"] - y["helpful"]) > 1)


def fmt(lab):
    return f"grounded {lab['grounded']}, helpful {lab['helpful']}, {lab['failure']}"


def new_label():
    g = int(ask("  Grounded (0/1): ", ["0", "1"]))
    h = int(ask("  Helpful (1-5): ", ["1", "2", "3", "4", "5"]))
    print("  Failure: " + "  ".join(f"{i}={n}" for i, n in enumerate(FAILURES)))
    f = FAILURES[int(ask("  Failure type number: ", [str(i) for i in range(len(FAILURES))]))]
    return {"grounded": g, "helpful": h, "failure": f}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", help="rater A file (full items, e.g. data/golden.jsonl)")
    ap.add_argument("b", help="rater B file (e.g. data/rater2.jsonl)")
    ap.add_argument("--out", help="where to write settled labels (default: update file A in place)")
    ap.add_argument("--log", default=os.path.join(HERE, "docs", "RULINGS_LOG.md"))
    args = ap.parse_args()

    items = load(args.a)
    b = {r["id"]: r["human"] for r in load(args.b)}
    todo = [it for it in items if it["id"] in b and differs(it["human"], b[it["id"]])]
    print(f"{len(todo)} disagreements to settle.\n")

    rulings, changed = [], 0
    for n, it in enumerate(todo, 1):
        la, lb = it["human"], b[it["id"]]
        print("=" * 70)
        print(f"Disagreement {n}/{len(todo)}  (id {it['id']})\n")
        print(f"CONTEXT:\n  {it['context']}\n")
        print(f"QUESTION:\n  {it['query']}\n")
        print(f"AGENT RESPONSE:\n  {it['response']}\n")
        print(f"  A: {fmt(la)}" + (f"   note: {la['note']}" if la.get("note") else ""))
        print(f"  B: {fmt(lb)}" + (f"   note: {lb['note']}" if lb.get("note") else ""))
        print()
        choice = ask("Decision: a = keep A, b = take B, n = new label, s = skip: ", ["a", "b", "n", "s"])
        if choice == "s":
            print("  Skipped.\n")
            continue
        if choice == "a":
            final, source = {k: la[k] for k in ("grounded", "helpful", "failure")}, "A"
        elif choice == "b":
            final, source = {k: lb[k] for k in ("grounded", "helpful", "failure")}, "B"
        else:
            final, source = new_label(), "new"

        ruling = input("Ruling for the guide (optional, Enter to skip): ").strip()
        final["settled"] = {"from": source, "was_a": fmt(la), "was_b": fmt(lb)}
        if ruling:
            final["settled"]["ruling"] = ruling
            rulings.append((it["id"], it["response"], ruling))
        if {k: la[k] for k in ("grounded", "helpful", "failure")} != {k: final[k] for k in ("grounded", "helpful", "failure")}:
            changed += 1
        it["human"] = final
        print(f"  Settled: {fmt(final)} (from {source})\n")

    out = args.out or args.a
    if out == args.a:
        shutil.copy(args.a, args.a + ".bak")
    with open(out, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")

    if rulings:
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        new_file = not os.path.exists(args.log)
        with open(args.log, "a") as f:
            if new_file:
                f.write("# Rulings log\n\nRulings made while settling disagreements. Copy settled ones into "
                        "Edge-case rulings in LABELING_GUIDE.md.\n\n| Date | Item | Response | Ruling |\n"
                        "| --- | --- | --- | --- |\n")
            for iid, resp, rule in rulings:
                f.write(f"| {date.today()} | {iid} | {resp[:60]} | {rule} |\n")

    print("=" * 70)
    print(f"Saved {out}" + (f" (backup: {args.a}.bak)" if out == args.a else ""))
    print(f"Labels changed in file A: {changed}.  Rulings logged: {len(rulings)}"
          + (f" -> {os.path.relpath(args.log, HERE)}" if rulings else ""))
    print("Re-check with: python3 compare_raters.py " + out + " " + args.b)


if __name__ == "__main__":
    main()
