"""Calibrate an AutoRater against human labels.

Usage:
  python calibrate.py --model mock
  python calibrate.py --model ollama/llama3.1
  python calibrate.py --model gpt-4o-mini --groundedness-prompt prompts/groundedness_v2.txt
"""
import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

from autorater.judge import judge
from autorater.metrics import (accuracy, cohen_kappa, hallucination_detection,
                               spearman, weighted_kappa)

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock", help="LiteLLM model string, or 'mock'")
    ap.add_argument("--golden", default=os.path.join(HERE, "data", "golden.jsonl"))
    ap.add_argument("--groundedness-prompt", help="path to a custom groundedness rubric")
    ap.add_argument("--helpfulness-prompt", help="path to a custom helpfulness rubric")
    ap.add_argument("--tag", default="", help="label for this run, e.g. 'rubric-v2'")
    args = ap.parse_args()

    g_rubric = open(args.groundedness_prompt).read() if args.groundedness_prompt else None
    h_rubric = open(args.helpfulness_prompt).read() if args.helpfulness_prompt else None

    items = load(args.golden)
    rows = []
    for it in items:
        g = judge("groundedness", it, args.model, g_rubric)
        h = judge("helpfulness", it, args.model, h_rubric)
        rows.append({
            "id": it["id"], "domain": it["domain"], "failure": it["human"]["failure"],
            "human_grounded": it["human"]["grounded"], "judge_grounded": int(g["grounded"]),
            "human_helpful": it["human"]["helpful"], "judge_helpful": int(h["helpful"]),
            "judge_reasoning": g.get("reasoning", ""), "response": it["response"],
            "note": it["human"].get("note", ""),
        })

    hg = [r["human_grounded"] for r in rows]
    jg = [r["judge_grounded"] for r in rows]
    hh = [r["human_helpful"] for r in rows]
    jh = [r["judge_helpful"] for r in rows]
    det = hallucination_detection(hg, jg)

    by_failure = defaultdict(lambda: [0, 0])  # caught, total (ungrounded items only)
    for r in rows:
        if r["human_grounded"] == 0:
            by_failure[r["failure"]][1] += 1
            by_failure[r["failure"]][0] += r["judge_grounded"] == 0

    summary = {
        "model": args.model, "tag": args.tag, "n": len(rows),
        "groundedness": {"accuracy": accuracy(hg, jg), "kappa": cohen_kappa(hg, jg), **det},
        "helpfulness": {
            "exact_match": accuracy(hh, jh),
            "within_1": sum(abs(a - b) <= 1 for a, b in zip(hh, jh)) / len(rows),
            "weighted_kappa": weighted_kappa(hh, jh),
            "spearman": spearman(hh, jh),
            "mean_bias": sum(b - a for a, b in zip(hh, jh)) / len(rows),
        },
        "recall_by_failure_type": {k: f"{c}/{t}" for k, (c, t) in by_failure.items()},
    }

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = args.model.replace("/", "_")
    out = os.path.join(HERE, "reports", f"{stamp}_{safe}{'_' + args.tag if args.tag else ''}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out + ".json", "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)

    g, h = summary["groundedness"], summary["helpfulness"]
    lines = [
        f"# AutoRater calibration: {args.model} {args.tag}".rstrip(), "",
        f"Items: {len(rows)}", "",
        "## Groundedness (binary)",
        f"- Accuracy: {g['accuracy']:.0%}   Cohen's kappa: {g['kappa']:.2f}",
        f"- Hallucination precision: {g['precision']:.0%}   recall: {g['recall']:.0%}"
        f"   (TP {g['tp']}, FP {g['fp']}, FN {g['fn']}, TN {g['tn']})",
        "- Recall by failure type: " + ", ".join(f"{k} {v}" for k, v in summary["recall_by_failure_type"].items()),
        "", "## Helpfulness (1-5)",
        f"- Exact: {h['exact_match']:.0%}   Within 1: {h['within_1']:.0%}   "
        f"Weighted kappa: {h['weighted_kappa']:.2f}   Spearman: {h['spearman']:.2f}",
        f"- Mean bias (judge minus human): {h['mean_bias']:+.2f}", "",
        "## Disagreements to review", "",
        "| id | failure | human g/h | judge g/h | response |", "|---|---|---|---|---|",
    ]
    for r in rows:
        if r["human_grounded"] != r["judge_grounded"] or abs(r["human_helpful"] - r["judge_helpful"]) > 1:
            lines.append(
                f"| {r['id']} | {r['failure']} | {r['human_grounded']}/{r['human_helpful']} | "
                f"{r['judge_grounded']}/{r['judge_helpful']} | {r['response'][:70]} |")
    report = "\n".join(lines) + "\n"
    with open(out + ".md", "w") as f:
        f.write(report)
    print(report)
    print(f"Saved {out}.md and .json")


if __name__ == "__main__":
    main()
