"""Merge human labels into candidates and split into dev (tune on) and test (report on) sets.

Usage:
  python3 merge_labels.py data/candidates.jsonl data/candidates_rater1.jsonl --holdout 0.3

Writes data/golden_dev.jsonl and data/golden_test.jsonl. Items without a label are skipped.
Also reports where the human label disagrees with the planted failure: review those first.
"""
import argparse
import json
import random


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("labels")
    ap.add_argument("--holdout", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--prefix", default="data/golden")
    args = ap.parse_args()

    labels = {r["id"]: r["human"] for r in load(args.labels)}
    merged, mismatches = [], []
    for item in load(args.candidates):
        if item["id"] not in labels:
            continue
        item["human"] = labels[item["id"]]
        merged.append(item)
        if "planted" in item and item["planted"] != item["human"]["failure"]:
            mismatches.append(item)

    # Split by scenario context, so near-duplicate variants of one scenario stay on the same side.
    groups = {}
    for item in merged:
        groups.setdefault(item["context"], []).append(item)
    keys = sorted(groups)
    random.Random(args.seed).shuffle(keys)
    n_test = round(len(keys) * args.holdout)
    test_keys = set(keys[:n_test])

    dev = [i for k in keys if k not in test_keys for i in groups[k]]
    test = [i for k in keys if k in test_keys for i in groups[k]]
    for name, rows in (("dev", dev), ("test", test)):
        with open(f"{args.prefix}_{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    print(f"Merged {len(merged)} labeled items: {len(dev)} dev, {len(test)} test (held out).")
    print(f"Human label differs from planted failure on {len(mismatches)} items:")
    for m in mismatches[:20]:
        print(f"  {m['id']}: planted {m['planted']}, labeled {m['human']['failure']}  \"{m['response'][:60]}\"")
    print(f"\nTune with:  python3 calibrate.py --golden {args.prefix}_dev.jsonl --model <m>")
    print(f"Report with: python3 calibrate.py --golden {args.prefix}_test.jsonl --model <m> --tag final")


if __name__ == "__main__":
    main()
