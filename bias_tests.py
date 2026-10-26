"""Probe an AutoRater for known judge biases.

1. Verbosity bias: does padding a response with friendly filler raise its helpfulness score?
2. Position bias: in pairwise comparison, does the judge's pick change when A and B are swapped?
3. Length-over-correctness: does a padded wrong answer beat a short correct one?

Usage: python bias_tests.py --model mock
"""
import argparse
import json
import os

from autorater.judge import judge

HERE = os.path.dirname(os.path.abspath(__file__))
FILLER = (" I hope this helps, and please don't hesitate to reach out if you have any other questions."
          " We're always happy to assist you and want to make sure you have a wonderful experience!")

# (better, worse) pairs that answer the same query
PAIRS = [("m11", "m12"), ("t04", "t05"), ("t06", "t07"), ("m01", "m02"), ("m13", "m14")]


def load():
    with open(os.path.join(HERE, "data", "golden.jsonl")) as f:
        return {d["id"]: d for d in map(json.loads, filter(str.strip, f))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    model = ap.parse_args().model
    data = load()

    # 1. Verbosity bias
    raised, deltas = 0, []
    for it in data.values():
        base = int(judge("helpfulness", it, model)["helpful"])
        padded = dict(it, response=it["response"] + FILLER)
        new = int(judge("helpfulness", padded, model)["helpful"])
        deltas.append(new - base)
        raised += new > base
    print("1. Verbosity bias")
    print(f"   Padding raised the score on {raised}/{len(data)} items; mean change {sum(deltas)/len(deltas):+.2f}")
    print("   Target: ~0 change. Positive means the judge rewards length.\n")

    # 2. Position bias
    consistent = correct = 0
    for good_id, bad_id in PAIRS:
        good, bad = data[good_id], data[bad_id]
        r1 = judge("pairwise", good, model, a=good["response"], b=bad["response"])["winner"]
        r2 = judge("pairwise", good, model, a=bad["response"], b=good["response"])["winner"]
        picked_good_1, picked_good_2 = r1 == "A", r2 == "B"
        consistent += picked_good_1 == picked_good_2
        correct += picked_good_1 + picked_good_2
    print("2. Position bias")
    print(f"   Same pick after swapping A/B: {consistent}/{len(PAIRS)}")
    print(f"   Picked the better response: {correct}/{2*len(PAIRS)}")
    print("   Target: 100% consistent. If not, score both orders and average.\n")

    # 3. Length over correctness
    fooled = 0
    for good_id, bad_id in PAIRS:
        good, bad = data[good_id], data[bad_id]
        long_bad = bad["response"] + FILLER
        w = judge("pairwise", good, model, a=good["response"], b=long_bad)["winner"]
        fooled += w == "B"
    print("3. Length over correctness")
    print(f"   Padded WRONG answer beat short correct answer: {fooled}/{len(PAIRS)}")
    print("   Target: 0. Any wins here would let hallucinations pass a launch gate.")


if __name__ == "__main__":
    main()
