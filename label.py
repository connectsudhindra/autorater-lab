"""Blind labeling tool: shows each item WITHOUT existing labels and records yours.

Usage:
  python3 label.py                          # writes data/rater2.jsonl
  python3 label.py --out data/rater3.jsonl  # a third labeler

Progress is saved after every item; re-run to resume where you stopped.
"""
import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
FAILURES = ["none", "contradiction", "fabricated_fact", "unsupported_claim", "policy_violation", "evasive"]


def ask(prompt, valid):
    while True:
        v = input(prompt).strip().lower()
        if v in valid:
            return v
        print(f"  Please enter one of: {', '.join(valid)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=os.path.join(HERE, "data", "golden.jsonl"))
    ap.add_argument("--out", default=os.path.join(HERE, "data", "rater2.jsonl"))
    args = ap.parse_args()

    with open(args.golden) as f:
        items = [json.loads(line) for line in f if line.strip()]
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(line)["id"] for line in f if line.strip()}

    todo = [it for it in items if it["id"] not in done]
    random.Random(7).shuffle(todo)  # shuffled so paired good/bad answers aren't side by side
    print(f"{len(done)} already labeled, {len(todo)} to go. Ctrl+C to stop; progress is saved.\n")

    for n, it in enumerate(todo, 1):
        print("=" * 70)
        print(f"Item {n}/{len(todo)}  (id {it['id']})\n")
        print(f"CONTEXT:\n  {it['context']}\n")
        print(f"QUESTION:\n  {it['query']}\n")
        print(f"AGENT RESPONSE:\n  {it['response']}\n")
        g = int(ask("Grounded? 1 = every claim supported, 0 = any claim unsupported: ", ["0", "1"]))
        h = int(ask("Helpful 1-5: ", ["1", "2", "3", "4", "5"]))
        print("Failure: " + "  ".join(f"{i}={name}" for i, name in enumerate(FAILURES)))
        fail = FAILURES[int(ask("Failure type number: ", [str(i) for i in range(len(FAILURES))]))]
        note = input("Note (optional, Enter to skip): ").strip()
        rec = {"id": it["id"], "human": {"grounded": g, "helpful": h, "failure": fail}}
        if note:
            rec["human"]["note"] = note
        with open(args.out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print()

    print(f"Done. Now run:\n  python3 compare_raters.py data/golden.jsonl {os.path.relpath(args.out, HERE)}")


if __name__ == "__main__":
    main()
