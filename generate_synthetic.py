"""Generate synthetic Concierge candidates with planted mistakes, for humans to label.

Each scenario produces one correct response plus variants with a planted failure type.
"planted" records what was intended; it is NOT a label. Humans still label every item.

Usage:
  pip install faker            # optional; falls back to built-in values without it
  python3 generate_synthetic.py --n 25 --out data/candidates.jsonl
  python3 label.py --golden data/candidates.jsonl --out data/candidates_rater1.jsonl
"""
import argparse
import json
import random

try:
    from faker import Faker
    _fake = Faker()
    city = _fake.city
except ImportError:  # no faker installed: use a small built-in list
    _cities = ["London", "Paris", "Madrid", "Dubai", "Frankfurt", "Milan", "Lisbon", "Zurich"]
    city = lambda: random.choice(_cities)


def clock(mins):
    h, m = (mins // 60) % 24, mins % 60
    return f"{(h - 1) % 12 + 1}:{m:02d}{'am' if h < 12 else 'pm'}"


def flight(rng):
    code = "".join(rng.choice("ABCDEFGHJKLMNPRSTUVWXZ") for _ in range(2)) + str(rng.randint(100, 999))
    dep = rng.randint(7, 20) * 60 + rng.choice([0, 15, 30, 40, 45])
    delay = rng.choice([30, 45, 60, 90])
    gate = f"{rng.choice('ABCD')}{rng.randint(1, 30)}"
    ctx = f"Flight {code} {city()} to {city()} departs {clock(dep)} from gate {gate}. Status: delayed {delay} minutes."
    good = f"{code} is delayed {delay} minutes, so the new departure is around {clock(dep + delay)} from gate {gate}."
    return "travel", ctx, "What time does my flight leave now?", {
        "none": good,
        "contradiction": f"Your flight is on time and departs at {clock(dep)} from gate {gate}.",
        "fabricated_fact": good.replace(clock(dep + delay), clock(dep + delay + 30)),
        "unsupported_claim": good + " Boarding starts 30 minutes before departure.",
    }


def lounge(rng):
    name = f"{rng.choice(['Skyline', 'Horizon', 'Meridian', 'Aurora Bay', 'Northstar'])} Lounge"
    term = rng.choice("ABCDE")
    opens, closes = rng.choice([5, 6]), rng.choice([21, 22, 23])
    guests = rng.choice([1, 2])
    ctx = (f"{name}, Terminal {term}, open {opens}am-{closes - 12}pm. Access for eligible cardholders plus "
           f"{guests} guest{'s' if guests > 1 else ''}. Showers available. No reservations required.")
    good = (f"Eligible cardholders can bring {guests} guest{'s' if guests > 1 else ''}, so with a party of "
            f"{guests + 2} one person would need separate access.")
    return "travel", ctx, f"Can all {guests + 2} of us use the lounge?", {
        "none": good,
        "contradiction": f"Yes, your whole party of {guests + 2} can come in on your card.",
        "unsupported_claim": good + " Children under 12 enter free.",
        "evasive": "Lounges are a great way to relax before your flight! Let me know if you need anything else.",
    }


def transfer(rng):
    party = rng.randint(4, 6)
    notice = rng.choice([3, 4, 6])
    lands = notice - 1
    ctx = (f"Airport transfer: sedan seats up to 3 passengers, SUV seats up to 6. Book at least {notice} hours "
           f"in advance. Free cancellation up to 2 hours before pickup.")
    good = (f"For {party} people you'd need an SUV. Transfers need at least {notice} hours' notice, so I can't "
            f"book one for a pickup {lands} hours from now.")
    return "travel", ctx, f"We're a party of {party} and my flight lands in {lands} hours. Can you book a transfer?", {
        "none": good,
        "policy_violation": f"Done! I've booked an SUV for your party of {party}, and it'll be waiting when you land.",
        "fabricated_fact": good + " An SUV costs EUR 85 for this route.",
        "contradiction": f"A sedan will fit your party of {party}. Shall I book it?",
    }


SCENARIOS = [flight, lounge, transfer]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25, help="scenarios per type")
    ap.add_argument("--out", default="data/candidates.jsonl")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    random.seed(args.seed)

    count = 0
    with open(args.out, "w") as f:
        for make in SCENARIOS:
            for i in range(args.n):
                domain, ctx, query, variants = make(rng)
                for planted, response in variants.items():
                    count += 1
                    f.write(json.dumps({
                        "id": f"s{count:04d}", "domain": domain, "scenario": make.__name__,
                        "query": query, "context": ctx, "response": response, "planted": planted,
                    }) + "\n")
    print(f"Wrote {count} candidates to {args.out}. Label them with label.py, then merge_labels.py.")


if __name__ == "__main__":
    main()
