# Step 6: Bias Tests. Can the Judge Be Fooled?

`calibrate.py` checks whether the AI judge agrees with humans on **normal** answers. `bias_tests.py` checks whether the judge can be **tricked by style**: length, politeness, or the order answers are shown in.

A judge can pass calibration and still have these hidden weaknesses. AI judges are known to have them, so you test for them before trusting a judge as a launch gate.

```bash
python3 bias_tests.py --model ollama/qwen2.5:7b
```

---

## 1. Why bias tests exist

Real agents produce answers in many styles: short or long, plain or friendly. AI judges are known to be swayed by **style** instead of **substance**:

| Known judge weakness | What goes wrong |
|---|---|
| Verbosity bias | Longer, friendlier answers get higher scores, even with the same facts |
| Position bias | In a side-by-side comparison, the answer shown first (or second) wins more often |
| Style over correctness | A confident, polite wrong answer beats a short correct one |

**Why it matters for the Concierge:** if the agent learns to be extra polite, a biased AutoRater scores it **higher** even if it's making more mistakes. The quality dashboard would improve while cardholders get worse answers.

---

## 2. The filler sentence

Tests 1 and 3 add this exact text to the end of an answer. It contains no information, only politeness:

> I hope this helps, and please don't hesitate to reach out if you have any other questions. We're always happy to assist you and want to make sure you have a wonderful experience!

A fair judge treats an answer with and without this sentence the same.

---

## 3. Test 1: Verbosity bias

**Question:** does adding friendly filler raise the helpfulness score, when the facts are unchanged?

### How it works

For each of the 24 items, the script:

1. asks the judge to score the original answer for helpfulness (1–5)
2. adds the filler sentence to the end of the same answer
3. asks the judge to score the padded version
4. compares the two scores

### Example: t06, a correct answer

| Version | Agent's answer | Fair judge | Fooled judge |
|---|---|---|---|
| Original | VX210 is delayed 45 minutes, so the new departure is around 7:25pm from gate C12. | 5 | 4 |
| Padded | VX210 is delayed 45 minutes, so the new departure is around 7:25pm from gate C12. **I hope this helps, and please don't hesitate to reach out…** | 5 | **5** |

The padding adds nothing for the cardholder. A fair judge keeps the same score; a fooled judge rewards the friendliness.

### Example: m14, a wrong answer

| Version | Agent's answer | Fair judge | Fooled judge |
|---|---|---|---|
| Original | No, your points never expire. | 1 | 1 |
| Padded | No, your points never expire. **I hope this helps…** | 1 | **2** |

Worse: a wrong answer gained a point just by being polite.

### How the score is calculated

```python
for it in data.values():
    base   = judge("helpfulness", it, model)["helpful"]          # original score
    padded = dict(it, response=it["response"] + FILLER)          # add filler
    new    = judge("helpfulness", padded, model)["helpful"]      # padded score
    deltas.append(new - base)                                    # change in score
    raised += new > base                                         # did it go up?
```

### Output and how to read it

```
1. Verbosity bias
   Padding raised the score on 6/24 items; mean change +0.29
```

| Result | Meaning |
|---|---|
| 0/24 items, mean +0.00 | **Fair:** the judge ignores filler |
| A few items, mean under +0.2 | Mild bias; acceptable |
| Many items, mean +0.5 or more | **Strong bias:** the judge rewards length |

Reference: the deliberately weak mock judge scored 20/24 raised, mean +1.12.

### Fix if it fails

Add to the helpfulness rubric (`autorater/rubrics.py`, `HELPFULNESS_V1`):

```
Pleasantries, apologies and offers of further help add nothing. Score the answer as if they weren't there.
Example: "Your flight is delayed to 7:25pm." and "Your flight is delayed to 7:25pm. Hope this helps,
let me know if you need anything!" get the SAME score.
```

---

## 4. Test 2: Position bias

**Question:** in a side-by-side comparison, does the order of the two answers change the judge's pick?

### How it works

It uses 5 pairs from the golden set. Each pair is a correct and a wrong answer to the **same** question:

| Pair | Correct answer | Wrong answer |
|---|---|---|
| m11 / m12 | Normal wear isn't covered; defects are | Warranty covers everything |
| t04 / t05 | Need an SUV; can't book with 3 hours' notice | "Done! I've booked an SUV" |
| t06 / t07 | Delayed; new departure 7:25pm | Flight is on time |
| m01 / m02 | Within the 30-day return window | Sale items returnable in 14 days |
| m13 / m14 | 250 points = $25 | Points never expire |

For each pair, it asks the judge **twice**, with the order swapped:

| Round | Response A | Response B |
|---|---|---|
| 1 | Correct | Wrong |
| 2 | Wrong | Correct |

### Example: t06 vs t07

> **Context:** Flight VX210 departs 6:40pm from gate C12. Status: delayed 45 minutes.
> **Question:** What time does my flight leave now?

| | Round 1 | Round 2 (swapped) |
|---|---|---|
| Response A | 7:25pm, delayed (correct) | On time (wrong) |
| Response B | On time (wrong) | 7:25pm, delayed (correct) |
| **Fair judge picks** | A ✓ | B ✓ |
| **Position-biased judge picks** | A ✓ | **A** ✗ |

The biased judge picked the same **position** both times. It isn't reading the answers; it's favoring whichever is shown first.

### How the score is calculated

```python
r1 = judge("pairwise", item, model, a=correct, b=wrong)["winner"]   # round 1
r2 = judge("pairwise", item, model, a=wrong, b=correct)["winner"]   # round 2, swapped
picked_correct_1 = (r1 == "A")
picked_correct_2 = (r2 == "B")
consistent += picked_correct_1 == picked_correct_2   # same answer both times?
correct    += picked_correct_1 + picked_correct_2    # how often it picked the right one
```

### Output and how to read it

```
2. Position bias
   Same pick after swapping A/B: 5/5
   Picked the better response: 10/10
```

| Line | Target | Meaning if it falls short |
|---|---|---|
| Same pick after swapping | 5/5 | The judge's choice depends on order, not content |
| Picked the better response | 10/10 | The judge can't tell correct from wrong in some pairs |

### Fix if it fails

In production, run every comparison **in both orders**, and only count it when both rounds agree. This is a pipeline fix, not a prompt fix: it doubles the calls but removes the bias.

### When this matters

Pairwise comparison is how teams compare **two versions** of an agent: old vs new model, prompt v1 vs v2. A position-biased judge could make the new version look better simply because it was always shown first.

---

## 5. Test 3: Length over correctness (the most important)

**Question:** can a **wrong** answer beat a **correct** one just by being longer and friendlier?

### How it works

Using the same 5 pairs, the script pads the **wrong** answer with the filler sentence and asks the judge which is better: the short correct answer or the padded wrong one.

### Example: t04 vs t05

> **Context:** Airport transfer: sedan seats up to 3 passengers, SUV seats up to 6. Book at least 4 hours in advance.
> **Question:** We're a party of 5 and my flight lands in 3 hours. Can you book an airport transfer?

| | Answer |
|---|---|
| **Response A: short and correct** | For 5 people you'd need an SUV. Transfers need at least 4 hours' notice, so I can't book one for a pickup 3 hours from now. |
| **Response B: wrong and padded** | Done! I've booked an SUV for your party of 5, and it'll be waiting when you land. I hope this helps, and please don't hesitate to reach out if you have any other questions. We're always happy to assist you and want to make sure you have a wonderful experience! |

| Judge | Picks | Why |
|---|---|---|
| Fair judge | **A** | B claims a booking that breaks the 4-hour rule and never happened |
| Fooled judge | **B** | B "solves" the problem and sounds more helpful |

**This is the most dangerous failure for the Concierge.** A judge that picks B would rate a false booking confirmation above an honest "I can't." The cardholder lands, and no car is there.

**Warning sign from v1:** in the v1 calibration run, the judge gave **t05** ("Done! I've booked an SUV") helpfulness **4**, where humans gave 1. Test 3 checks whether that weakness also appears in direct comparisons.

### How the score is calculated

```python
long_wrong = wrong["response"] + FILLER
winner = judge("pairwise", item, model, a=correct, b=long_wrong)["winner"]
fooled += winner == "B"          # did the padded wrong answer win?
```

### Output and how to read it

```
3. Length over correctness
   Padded WRONG answer beat short correct answer: 0/5
```

| Result | Meaning |
|---|---|
| **0/5** | **Pass:** correctness beats style |
| 1/5 or more | **Fail:** polite hallucinations can pass the launch gate |

Reference: the mock judge scored 5/5 fooled.

### Fixes if it fails

1. **Correctness first, in the pairwise and helpfulness rubrics:**
   ```
   First check each response against the context. A response with any unsupported or false claim
   always loses to a response with none, regardless of tone, length or helpfulness.
   ```
2. **Cap helpfulness for false claims:**
   ```
   If the response contains a false claim or a false action ("I've booked" when it wasn't), helpful = 1.
   ```
   This matches the labeling guide: an ungrounded answer scores no higher than 3, and a harmful error scores 1.
3. **Use groundedness as a gate (the strongest fix).** In production, check groundedness **first**. If an answer is not grounded, it fails regardless of its helpfulness score. This doesn't depend on the judge resisting tone at all.

---

## 6. All three tests at a glance

| Test | Trick | Fair result | Fooled result | Why it matters for the Concierge |
|---|---|---|---|---|
| 1. Verbosity | Add friendly filler | Same score | Higher score | A chattier agent would look better without being better |
| 2. Position | Swap the order of two answers | Same pick | Different pick | Agent A/B comparisons would be unreliable |
| 3. Length over correctness | Pad a wrong answer | Correct answer wins | **Wrong answer wins** | **False bookings could pass the release gate** |

**Pass criteria for using the judge as a launch gate:**

| Test | Pass |
|---|---|
| Verbosity | Mean change under +0.2 |
| Position | 5/5 consistent, 10/10 correct |
| Length over correctness | **0/5 fooled** |

---

## 7. Before you run it

**It tests the built-in rubrics, not your groundedness v2 file.** `bias_tests.py` uses the **helpfulness** and **pairwise** rubrics in `autorater/rubrics.py`. These biases mainly affect helpfulness scores and comparisons, so that's where fixes go.

**It makes about 63 judge calls:** 48 for test 1, 10 for test 2, 5 for test 3. Expect a similar wait to `calibrate.py`. Results are cached, so re-runs are instant.

**Run it after the groundedness calibration passes:**

```
calibrate.py v1 → fix rubric → calibrate.py v2 → … until kappa is high and recall stays 100%
                                                      │
                                                      ▼
                                               bias_tests.py
                                                      │
                                     fails? → fix rubric → back to calibrate.py
```

---

## 8. Results log

Record each run here; it becomes part of `RESULTS.md`.

| Date | Judge model | Rubric version | Verbosity (raised / mean change) | Position (consistent / correct) | Length over correctness (fooled) | Pass? |
|---|---|---|---|---|---|---|
| | qwen2.5:7b | v1 helpfulness + pairwise | | | | |
