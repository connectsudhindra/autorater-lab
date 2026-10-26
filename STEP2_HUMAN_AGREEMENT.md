# Step 2: Check Human Agreement

Before an AutoRater can be graded against human labels, the human labels themselves must be consistent. Step 2 measures how well two human raters agree, using **Cohen's kappa**, and fixes the labeling guide wherever they don't.

This document walks through the lab's actual result: **22 of 24 items agreed, grounded kappa 0.83.**

---

## 1. Why this step exists

The AutoRater is scored against human labels. If two humans would label the same answer differently, the AutoRater's score depends on *which* human wrote the label, not on how good the judge is.

Think of it as checking the ruler before measuring anything with it.

**Example: m10**

> **Context:** TrailLite 2 tent, waterproof rating 3000mm, $249.
> **Question:** Is the TrailLite 2 good in the rain?
> **Agent:** Yes, it has a 3000mm waterproof rating, which handles heavy rain well.

| Rater | Grounded | Reason |
|---|---|---|
| A | 1 | "Handles heavy rain" is a fair reading of 3000mm |
| B | 0 | The context never says "heavy rain"; it's a quality judgment |

If the AutoRater says 0, it is *right* against B and *wrong* against A. Until the raters agree on a rule, there is no single right answer to measure the judge against.

**What skipping this step costs:** if humans only agree at kappa 0.70 and the AutoRater also scores 0.70, the judge is already as good as a second human. Without knowing the human number, you'd wrongly conclude the judge is weak and spend days "fixing" a rubric that was never the problem.

> **Human-vs-human agreement is the ceiling.** An AutoRater cannot meaningfully beat it.

---

## 2. Who the raters are

| Rater | File | Whose labels |
|---|---|---|
| **A** | `data/golden.jsonl` | The labels that ship with the lab |
| **B** | `data/rater2.jsonl` | The second rater, created with `python3 label.py` |

The order comes from the command: the first file is A, the second is B.

```bash
python3 compare_raters.py data/golden.jsonl data/rater2.jsonl
#                          └──── A ────────┘  └──── B ────────┘
```

`label.py` shows each item **without** existing labels (blind labeling), so B's judgment isn't influenced by A's.

---

## 3. The result

```
Items in both files: 24

Grounded:  agree 92%   kappa 0.83
Helpful:   exact 79%   within 1 100%   weighted kappa 0.96
Failure:   agree 88%   kappa 0.82

Disagreements to settle (rater A vs rater B: grounded/helpful/failure):

  m10: A 1/4/none   B 0/3/unsupported_claim
  t08: A 0/3/unsupported_claim   B 1/4/none
  t10: A 0/2/fabricated_fact   B 0/2/unsupported_claim
```

| Line | Meaning | Verdict |
|---|---|---|
| Grounded: kappa 0.83 | 22 of 24 matched; well above chance | Passes the 0.8 target |
| Helpful: weighted kappa 0.96 | Scores sometimes differ by 1, never by more | Very strong |
| Failure: kappa 0.82 | 21 of 24 chose the same mistake type | Good |

---

## 4. Side by side: all 24 grounded labels

| # | Item | Agent's answer (short) | A | B | Same? |
|---|---|---|---|---|---|
| 1 | m01 | Within 30-day window, bring receipt | 1 | 1 | ✓ |
| 2 | m02 | Sale items returnable in 14 days | 0 | 0 | ✓ |
| 3 | m03 | 3–5 days; under free-shipping threshold | 1 | 1 | ✓ |
| 4 | m04 | Standard shipping is $5.99 | 0 | 0 | ✓ |
| 5 | m05 | Closed 7pm Sunday | 1 | 1 | ✓ |
| 6 | m06 | Open New Year's Day | 0 | 0 | ✓ |
| 7 | m07 | "We value your business!" | 1 | 1 | ✓ |
| 8 | m08 | In stock Austin, Denver, not Seattle | 1 | 1 | ✓ |
| 9 | m09 | Tent weighs 1.2 kg | 0 | 0 | ✓ |
| 10 | m10 | Handles heavy rain well | **1** | **0** | ✗ |
| 11 | m11 | Wear not covered; defects are | 1 | 1 | ✓ |
| 12 | m12 | Warranty covers everything | 0 | 0 | ✓ |
| 13 | m13 | 250 points = $25 | 1 | 1 | ✓ |
| 14 | m14 | Points never expire | 0 | 0 | ✓ |
| 15 | t01 | Only one guest allowed | 1 | 1 | ✓ |
| 16 | t02 | Showers need 24-hour booking | 0 | 0 | ✓ |
| 17 | t03 | Lounge closed at midnight | 1 | 1 | ✓ |
| 18 | t04 | Need SUV; can't book with 3 hours' notice | 1 | 1 | ✓ |
| 19 | t05 | "I've booked an SUV" | 0 | 0 | ✓ |
| 20 | t06 | Delayed; new departure 7:25pm | 1 | 1 | ✓ |
| 21 | t07 | Flight is on time | 0 | 0 | ✓ |
| 22 | t08 | 10 kg bag plus personal item | **0** | **1** | ✗ |
| 23 | t09 | Openings 7pm and 8:30pm | 1 | 1 | ✓ |
| 24 | t10 | Five-course tasting menu | 0 | 0 | ✓ |

**Grouped:**

| Group | Count | Items |
|---|---|---|
| Both said 1 | 12 | m01, m03, m05, m07, m08, m11, m13, t01, t03, t04, t06, t09 |
| Both said 0 | 10 | m02, m04, m06, m09, m12, m14, t02, t05, t07, t10 |
| A said 1, B said 0 | 1 | m10 |
| A said 0, B said 1 | 1 | t08 |
| **Total** | **24** | |

---

## 5. How kappa is calculated

### The idea in one line

> Kappa measures how much better than **random guessing** two raters agree.

Raw agreement is misleading, because two raters who guess at random still agree part of the time. Kappa removes that "free" agreement.

### A tiny example first (10 answers)

| Answer | You | Friend | Same? |
|---|---|---|---|
| 1–4 | Good | Good | ✓ ✓ ✓ ✓ |
| 5 | Good | Bad | ✗ |
| 6–9 | Bad | Bad | ✓ ✓ ✓ ✓ |
| 10 | Bad | Good | ✗ |

- Agreement: 8 of 10 = **80%**
- Two coin flips match about half the time, so guessing gives **50%**
- Room above guessing: 100 − 50 = 50 points. Achieved above guessing: 80 − 50 = 30 points.

```
kappa = 30 ÷ 50 = 0.6
```

### The lab's real numbers (24 answers)

**Step 1: Count from the side-by-side table.**

| What to count | Result |
|---|---|
| Rows that match (✓) | 22 |
| Rows that differ (✗) | 2 (m10, t08) |
| A's 1s / 0s | 13 / 11 |
| B's 1s / 0s | 13 / 11 |

**Step 2: Actual agreement (pₒ).**

```
pₒ = 22 ÷ 24 = 0.917   (92%)
```

**Step 3: Agreement by luck (pₑ).** If each rater picked 1 or 0 at random, at the same rates they actually used:

```
Chance both pick 1  = (13 ÷ 24) × (13 ÷ 24) = 0.542 × 0.542 = 0.293
Chance both pick 0  = (11 ÷ 24) × (11 ÷ 24) = 0.458 × 0.458 = 0.210

pₑ = 0.293 + 0.210 = 0.503   (50%)
```

**Step 4: Kappa.**

```
κ = (pₒ − pₑ) ÷ (1 − pₑ)
  = (0.917 − 0.503) ÷ (1 − 0.503)
  = 0.414 ÷ 0.497
  = 0.83
```

**In words:** the raters agreed on 92%; guessing would give 50%; they covered **83% of the distance from guessing to perfect agreement.**

### Why kappa beats a plain percentage: the lazy rater

A rater who marks every answer "grounded" without reading:

| | Value |
|---|---|
| Agreement with A | 13 ÷ 24 = **54%** (looks half-decent) |
| pₑ | (13/24 × 24/24) + (11/24 × 0/24) = 0.542 |
| Kappa | (0.542 − 0.542) ÷ (1 − 0.542) = **0.00** |

Kappa correctly shows the lazy rater adds no information.

### How each disagreement moves kappa (24 items)

| Disagreements | Agreement | Kappa (approx.) |
|---|---|---|
| 0 | 24/24 | 1.00 |
| 2 (this result) | 22/24 | 0.83 |
| 4 | 20/24 | 0.66 |
| 6 | 18/24 | 0.50 |

On 24 items, each disagreement costs about 0.08 kappa. On 200 items, each matters far less, so the number is more stable.

---

## 6. Kappa for all three labels

| Label | Choices | Measure | Lab result |
|---|---|---|---|
| Grounded | 2 (0, 1) | Cohen's kappa | 0.83 |
| Failure type | 6 types | Cohen's kappa (luck summed over all 6 types) | 0.82 |
| Helpful | 1–5 scale | **Weighted** kappa | 0.96 |

**Why helpful uses weighted kappa:** plain kappa treats 5-vs-4 the same as 5-vs-1. Weighted kappa gives partial credit, with a penalty that grows with the square of the distance:

| Off by | Penalty |
|---|---|
| 0 | none |
| 1 | 1/16 |
| 2 | 4/16 |
| 3 | 9/16 |
| 4 | 16/16 (full) |

That's why helpful shows only 79% exact agreement but weighted kappa 0.96: raters often differed by 1, never by more.

**The same math is reused later:** `compare_raters.py` compares human vs human (step 2); `calibrate.py` compares the AutoRater vs human (steps 4–7).

---

## 7. Reading kappa

| Kappa | Meaning | Action |
|---|---|---|
| Below 0 | Worse than guessing; systematic disagreement | Check that raters are using the same guide |
| 0–0.4 | Weak | Rewrite unclear definitions; relabel |
| 0.4–0.6 | Moderate | Fix the most common disagreement types |
| 0.6–0.8 | Substantial | Settle disagreements, add rulings, continue |
| **0.8–1.0** | **Strong** | **Proceed to step 3** |

**Cautions**

1. **A perfect 1.0 is suspicious.** Check for copied labels, or items too easy to test anything.
2. **The human kappa is the AutoRater's ceiling.** With humans at 0.83, an AutoRater at 0.80 is excellent.
3. **Kappa isn't the only number.** For the AutoRater, also track **hallucination recall**: the share of bad answers it catches. A missed false booking matters more than a small kappa difference.

---

## 8. Settling the disagreements

For each disagreement: re-read the item against the labeling guide, decide who is right, then fix the label or add a ruling.

| Item | A | B | Guide says | Decision | Action |
|---|---|---|---|---|---|
| **m10** heavy rain | 1 / none | 0 / unsupported_claim | Ruling 1: quality judgments are unsupported unless the context states them | **B is right** | Change m10 in `golden.jsonl` to `grounded 0, helpful 3, unsupported_claim`; mark ruling 1 settled |
| **t08** personal item | 0 / unsupported_claim | 1 / none ("standard on most airlines") | General knowledge does not count as supported | **A is right** | Keep the label; add t08 as an example of the general-knowledge mistake |
| **t10** five courses | 0 / fabricated_fact | 0 / unsupported_claim | fabricated_fact = an invented specific value (number, time, price, name) | **A is right** | Keep the label; add ruling: an invented number or count is fabricated_fact |

After fixing m10, the golden set has 12 grounded and 12 not-grounded items.

---

## 9. What "grounded = 1" does and doesn't mean

**Grounded = 1 means the agent didn't make anything up: every claim is supported by the context.** It does not mean the answer is correct in the real world, or helpful.

| Case | Example | Grounded | Correct in reality | Helpful |
|---|---|---|---|---|
| Normal | Context: delayed 45 min. Agent: "new departure about 7:25pm" | 1 | Yes | 5 |
| Stale source | The airline tool still says 45 min, but the real delay is 2 hours. Agent: "about 7:25pm" | 1 | **No** | 5 |
| Says nothing | Agent: "Thanks for reaching out, we value your business!" | 1 | n/a | **1** |
| Adds general knowledge | Context: 1 bag up to 10 kg. Agent: "plus a personal item" | **0** | Maybe | 3 |

| Question | Checked by |
|---|---|
| Did the agent stick to its sources? | Grounded label |
| Did it actually help the cardholder? | Helpful label |
| Are the sources correct and current? | Data quality checks on vendor tools, outside the AutoRater |

---

## 10. A Concierge example (illustrative)

> This scenario is illustrative, not real data. It shows the kind of disagreement step 2 surfaces in a multi-vendor concierge.

**Context the agent had:**
- Airline tool: Flight VX210 arriving LHR, scheduled 7:30pm, delayed 45 minutes, new arrival 8:15pm.
- Car-service tool: Pickup change request for booking #4471 to 8:15pm. Status: **pending vendor confirmation**.

**Cardholder:** My flight's late, will my car still be there?
**Agent:** No problem. I've moved your pickup to 8:15pm, so your driver will be waiting.

| | Rater A | Rater B |
|---|---|---|
| Grounded | 1 | 0 |
| Failure | none | policy_violation |
| Reason | The tool shows 8:15pm | Status is *pending*; "I've moved it" promises an unconfirmed outcome |

**Resolution:** an action is only done when the vendor confirms it. New guide ruling:

| Case | Ruling |
|---|---|
| Vendor action with status pending | The agent must say it's pending ("I've requested 8:15pm; I'll confirm once the car service accepts"). Stating or implying it's complete is policy_violation. |

The same rule then goes into the AutoRater rubric in step 3, so the judge catches false confirmations.

---

## 11. In the real world

You don't hand-label thousands of items. Humans label a small set once to prove the AutoRater grades like a human; the AutoRater then grades everything.

| Who | How many | How often |
|---|---|---|
| Humans | 200–500 items | Once for the golden set, plus small audits |
| AutoRater | Thousands to millions | Every release, every day |

**A practical setup for a 200-item Concierge golden set:**

| Role | Who | Load |
|---|---|---|
| Rater 1 | A Concierge engineer | All 200 items (about 3–4 hours) |
| Rater 2 | A support agent or product owner | 60 of the same items (about 1 hour) |
| Adjudicator | Engineering manager or product owner | Settles disagreements; writes new rulings |

Pairing an engineer with someone outside engineering is deliberate: engineers tend to grade their own agent kindly, while support staff grade like cardholders.

---

## 12. Checklist: step 2 is done when

- [ ] Both raters labeled the same items blind
- [ ] `compare_raters.py` shows grounded kappa ≥ 0.8
- [ ] Every disagreement is settled: label fixed or ruling added
- [ ] New rulings are added to `docs/LABELING_GUIDE.md`
- [ ] `golden.jsonl` reflects the settled labels (m10 fixed)

**Next:** step 3, turning the labeling guide into the AutoRater rubric.
