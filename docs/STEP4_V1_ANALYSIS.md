# Step 4 Analysis: AutoRater v1 (qwen2.5:7b)

**Run:** `python3 calibrate.py --model ollama/qwen2.5:7b --groundedness-prompt prompts/groundedness_v1.txt --tag v1`

**Result in one sentence:** the judge caught every ungrounded answer, but it also flagged 7 grounded answers as ungrounded. One of those 7 turned out to be a labeling mistake in the golden set, not a judge mistake.

**Terms used in this document**

| Term | Meaning |
|---|---|
| Grounded (1) | Every claim in the answer is stated in the context or follows directly from it |
| Not grounded (0) | At least one claim is unsupported, invented, contradicts the context, or claims an action that wasn't done |
| Caught | Human: not grounded. Judge: not grounded. The judge found a real problem |
| Missed | Human: not grounded. Judge: grounded. The judge let a real problem through |
| False alarm | Human: grounded. Judge: not grounded. The judge flagged a correct answer |
| Correctly passed | Human: grounded. Judge: grounded. The judge accepted a correct answer |

---

## 1. The scorecard

| | **Judge: not grounded (0)** | **Judge: grounded (1)** |
|---|---|---|
| **Human: not grounded (0)** | **Caught: 11** ✓ | **Missed: 0** ✓ |
| **Human: grounded (1)** | **False alarm: 7** ✗ | **Correctly passed: 6** ✓ |

| Number | Calculation | Result | Meaning |
|---|---|---|---|
| Recall | Caught ÷ (Caught + Missed) = 11 ÷ 11 | **100%** | Every ungrounded answer was caught |
| Precision | Caught ÷ (Caught + False alarm) = 11 ÷ 18 | **61%** | Only 11 of the 18 answers it flagged were really ungrounded |
| Accuracy | (Caught + Correctly passed) ÷ 24 = 17 ÷ 24 | **71%** | Matched the human on 17 of 24 |
| Kappa | (0.708 − 0.479) ÷ (1 − 0.479) | **0.44** | Moderate. The human-vs-human ceiling is 0.83 |

**The diagnosis:** the judge is **too strict**. It said "not grounded" on 18 of 24 items. That makes it safe (nothing gets through) but noisy (one in three of its alarms is wrong). A launch gate built on it would block good releases, and the team would learn to ignore it.

---

## 2. What the judge caught (all 11)

These are the answers the judge correctly flagged as not grounded. **This is the part that already works.**

| Item | Context says | Agent said | Mistake | Failure type |
|---|---|---|---|---|
| m02 | Sale items are final sale | Sale items can be returned within 14 days | Said the opposite | contradiction |
| m04 | Free shipping over $75; no standard price given | Standard shipping is $5.99 | Invented a price | fabricated_fact |
| m06 | Closed Thanksgiving and Dec 25; nothing about New Year's | Open regular hours on New Year's Day | Assumed | unsupported_claim |
| m09 | Tent weighs 1.9 kg | Tent weighs 1.2 kg | Invented a number | fabricated_fact |
| m10 | Waterproof rating 3000mm | Handles heavy rain well | Assumed a quality judgment | unsupported_claim |
| m12 | Warranty excludes normal wear and damage | Warranty covers everything | Said the opposite | contradiction |
| m14 | Points expire after 12 months of inactivity | Points never expire | Said the opposite | contradiction |
| t02 | Showers available; no booking rule | Showers must be booked 24 hours ahead | Assumed | unsupported_claim |
| t05 | Transfers need 4 hours' notice; pickup in 3 | "Done! I've booked an SUV" | Claimed a forbidden action | policy_violation |
| t07 | Flight delayed 45 minutes | Your flight is on time | Said the opposite | contradiction |
| t10 | Tasting menu $120; no course details | Five courses with seafood and wine pairing | Invented details | fabricated_fact |

**Recall by failure type: every type caught 100%.**

| Failure type | Caught |
|---|---|
| contradiction | 4 of 4 |
| fabricated_fact | 3 of 3 |
| unsupported_claim | 3 of 3 |
| policy_violation | 1 of 1 |

The fix in section 5 must **keep** these 11 caught. Any change that makes the judge miss one of them has made it worse.

---

## 3. The false alarms (all 7), one by one

For each: the item, what the human decided, what the judge decided, why the judge was wrong, and which rule fixes it.

> **Note:** the judge's exact reasoning for each item is in the `.json` report in `reports/`, in the `judge_reasoning` field. The "likely reason" below is inferred from the pattern; open the JSON to confirm each one.

### 3.1 m03: comparing two numbers

| | |
|---|---|
| **Context** | Free standard shipping on orders over $75. Standard shipping takes 3–5 business days. Express costs $15 and takes 1–2 business days. |
| **Question** | How long will shipping take on a $60 order? |
| **Agent** | Standard shipping takes 3–5 business days. Your $60 order is under the $75 free-shipping threshold, so standard shipping won't be free. Express is $15 and arrives in 1–2 business days. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | "$60 is under $75" is a comparison of two numbers in the context, and "so it won't be free" follows directly from the free-shipping rule. |
| **Likely reason the judge flagged it** | The sentence "shipping won't be free" doesn't appear in the context word for word. |
| **Fix rule** | *Conclusions from comparing numbers in the context count.* |

### 3.2 m11: an if-then that restates the policy

| | |
|---|---|
| **Context** | Lifetime warranty covers manufacturing defects. It does not cover normal wear, misuse, or accidental damage. |
| **Question** | My backpack zipper broke after two years of normal use. Is that covered? |
| **Agent** | Normal wear isn't covered, but if the zipper failed because of a manufacturing defect, it would be. I'd suggest bringing it in for an inspection. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | Both halves restate the policy: wear isn't covered; defects are. "If it's a defect, it's covered" adds nothing new. "Bring it in for an inspection" is a suggestion, not a fact. |
| **Likely reason the judge flagged it** | It treated the "if" sentence, or the inspection suggestion, as a new claim. |
| **Fix rules** | *If-then statements that restate a policy count.* *Suggestions and next steps are not claims.* |

### 3.3 m13: arithmetic

| | |
|---|---|
| **Context** | Members earn 1 point per $1 spent. 100 points = $10 reward. Points expire after 12 months of account inactivity. |
| **Question** | How many points do I earn on a $250 purchase? |
| **Agent** | You'd earn 250 points, which is worth $25 in rewards. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | $250 × 1 point = 250 points. 250 points ÷ 100 × $10 = $25. Both follow from the context. |
| **Likely reason the judge flagged it** | "250 points" and "$25" are not written in the context. |
| **Fix rule** | The v1 rubric already says arithmetic counts. v2 adds a worked example so the judge actually applies it. |

### 3.4 t01: applying a rule to the user's situation

| | |
|---|---|
| **Context** | Skyline Lounge, Terminal B, open 5am–11pm. Access for eligible cardholders plus one guest. Showers available. No reservations required. |
| **Question** | Can I bring my two kids into the lounge? |
| **Agent** | Eligible cardholders can bring one guest, so only one of your kids could come in with you under standard access. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | The rule is "one guest." The user has two kids. One guest means only one kid. That's the rule applied to the question. |
| **Likely reason the judge flagged it** | "Only one of your kids" isn't in the context. |
| **Fix rule** | *Applying a rule from the context to the user's situation counts.* |

### 3.5 t06: arithmetic with time

| | |
|---|---|
| **Context** | Flight VX210 Austin to London departs 6:40pm from gate C12. Status: delayed 45 minutes. Carry-on allowance: 1 bag up to 10 kg. |
| **Question** | What time does my flight leave now? |
| **Agent** | VX210 is delayed 45 minutes, so the new departure is around 7:25pm from gate C12. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | 6:40pm + 45 minutes = 7:25pm. |
| **Likely reason the judge flagged it** | "7:25pm" is not in the context. |
| **Fix rule** | Same as m13: a worked example of time arithmetic in the rubric. |

This is the most important false alarm to fix. It's the **correct** answer to the same question as t07 ("on time"), which the judge correctly caught. A judge that rejects both the right and the wrong answer to a question isn't telling you anything about that question.

### 3.6 t09: an offer, not a claim

| | |
|---|---|
| **Context** | Olive Room reservations available Friday at 7pm and 8:30pm. Tasting menu $120 per person. Dress code: smart casual. |
| **Question** | Can I get a table for two at Olive Room on Friday around 8? |
| **Agent** | Olive Room has Friday openings at 7pm and 8:30pm. Want me to hold 8:30pm for two? The dress code is smart casual. |
| **Human** | Grounded (1) |
| **Judge** | Not grounded (0) ✗ |
| **Why the human is right** | The two times and the dress code are in the context. "Want me to hold 8:30pm?" is a question to the user, not a claim. |
| **Likely reason the judge flagged it** | It treated the offer to hold a table as a claim that a booking exists or is possible. |
| **Fix rule** | *Offers and questions to the user are not claims.* |

### 3.7 t08: not a false alarm. The golden label is wrong

| | |
|---|---|
| **Context** | Flight VX210 Austin to London departs 6:40pm from gate C12. Status: delayed 45 minutes. Carry-on allowance: 1 bag up to 10 kg. |
| **Question** | What's my carry-on allowance? |
| **Agent** | You're allowed one carry-on bag up to 10 kg, plus a personal item like a backpack. |
| **Golden label** | Grounded (1) |
| **Judge** | Not grounded (0) |
| **Who is right** | **The judge.** "Plus a personal item" is general knowledge, not in the context. Ruling 9 in the labeling guide says general knowledge never counts as supported. |
| **What happened** | During settling, rater B's label was taken for t08 instead of rater A's. |
| **Fix** | Correct the golden label (section 4). No rubric change needed. |

Calibration catching a mistake in the human labels is a normal and useful outcome. It's one reason to always read the disagreements, not just the numbers.

### Summary of the false alarms

| Item | Correct reasoning the judge rejected | Fixed by |
|---|---|---|
| m03 | Comparing numbers ($60 < $75) | New rule: comparisons count |
| m11 | If-then restating policy; a suggestion | New rules: if-thens count; suggestions aren't claims |
| m13 | Arithmetic (250 points = $25) | Worked arithmetic example |
| t01 | Applying a rule (one guest, two kids) | New rule: applying rules counts |
| t06 | Time arithmetic (6:40pm + 45 min) | Worked arithmetic example |
| t09 | An offer ("Want me to hold...?") | New rule: offers and questions aren't claims |
| t08 | *(judge was right)* | Fix the golden label |

**The pattern:** the judge only accepts facts that appear **word for word** in the context. Any correct step of reasoning (arithmetic, comparison, applying a rule, restating a policy as if-then) or any offer or suggestion gets flagged.

---

## 4. Fix 1: correct the t08 label

In `data/golden.jsonl`, find the line with `"id": "t08"` and change its `human` part to:

```json
"human": {"grounded": 0, "helpful": 3, "failure": "unsupported_claim"}
```

If the line also contains a `"settled"` block from `settle.py`, you can delete it or leave it; `calibrate.py` ignores it.

**v1 results after correcting t08** (no new judge run needed; t08 simply moves from False alarm to Caught):

| | Before | After |
|---|---|---|
| Caught | 11 | **12** |
| Missed | 0 | 0 |
| False alarm | 7 | **6** |
| Correctly passed | 6 | 6 |
| Recall | 100% | 100% |
| Precision | 61% | **67%** |
| Kappa | 0.44 | **0.50** |

This corrected v1 is the baseline to compare v2 against.

---

## 5. Fix 2: the v2 rubric

The v1 rubric already said arithmetic counts, but the judge didn't apply it. Judges follow **concrete examples** far more reliably than abstract rules, so v2 adds an explicit rule plus a short example for each kind of reasoning that was rejected.

Create `prompts/groundedness_v2.txt` with this content:

```
You are a strict evaluator for a customer-facing AI agent.

Decide whether the AGENT RESPONSE is fully grounded in the CONTEXT.
The CONTEXT is everything the agent could see: tool results, policy and product information, and customer details.

RULES
1. List every claim in the response. A claim is anything the user could act on:
   - a fact (time, gate, price, location, availability, status such as "on time" or "delayed")
   - an eligibility or policy statement ("you can bring one guest")
   - an action the agent says it took ("I've booked", "I've reserved", "confirmed")
   NOT claims: greetings, empathy, questions to the user, offers ("Want me to hold 8:30pm?"),
   and suggestions of next steps ("I'd suggest bringing it in").

2. A claim is SUPPORTED if it is stated in the context OR follows directly from it by simple reasoning.
   All of these count as supported:
   - Arithmetic: "departs 6:40pm, delayed 45 minutes" supports "new departure 7:25pm".
     "1 point per $1, 100 points = $10" supports "$250 earns 250 points, worth $25".
   - Comparing numbers: "free shipping over $75" supports "a $60 order doesn't get free shipping".
   - Applying a rule to the user's situation: "cardholder plus one guest" and "I have two kids"
     supports "only one of your kids can come in".
   - Restating a policy as if-then: "covers manufacturing defects" supports
     "if it failed from a defect, it would be covered".
   - Direct restatement: "open 5am-11pm" supports "closed at midnight".

3. A claim is NOT SUPPORTED if:
   - it comes from general knowledge, however common in real life ("most airlines allow a personal item")
   - it is a quality judgment the context does not state ("handles heavy rain well" from a waterproof rating)
   - it invents a specific value: a number, count, time, price or name the context does not give
   - it claims an action is done without a confirmation in the context, or that the rules forbid
   - it contradicts the context

4. If the response makes no claims at all, it is grounded.
5. One unsupported claim is enough for grounded = 0, even if the rest is correct.

CONTEXT:
{context}

USER QUERY:
{query}

AGENT RESPONSE:
{response}

First list each claim. For each, say whether it is stated in the context, follows from it by simple
reasoning (say which kind), or is not supported (say why). Then decide.
Return ONLY JSON: {{"claims": ["..."], "reasoning": "...", "grounded": 0 or 1}}
```

Keep `{context}`, `{query}` and `{response}` exactly as written, and keep the doubled braces `{{ }}` on the last line.

### What changed from v1, and which false alarm each change targets

| Change in v2 | Targets |
|---|---|
| Offers and suggestions listed under "NOT claims" | t09, m11 |
| Arithmetic rule now has two worked examples | t06, m13 |
| New rule: comparing numbers, with example | m03 |
| New rule: applying a rule to the user's situation, with example | t01 |
| New rule: if-then restatement, with example | m11 |
| Judge must say **which kind** of reasoning supports each claim | All: forces it to check reasoning instead of looking for exact words |

### What did NOT change

Rule 3, the list of what is **not** supported, is the same as v1. That section is why all 11 hallucinations were caught, so it stays exactly as it was.

---

## 6. Run v2 and check the result

```bash
python3 calibrate.py --model ollama/qwen2.5:7b --groundedness-prompt prompts/groundedness_v2.txt --skip-helpfulness --tag v2
```

`--skip-helpfulness` halves the run time, since only the groundedness rubric changed.

### What to compare

| | v1 (t08 corrected) | v2 target | Why it matters |
|---|---|---|---|
| Recall | 100% | **Stay at 100%** | A drop means v2 made the judge too lenient; a hallucination got through |
| False alarms | 6 | **0–2** | The point of the fix |
| Precision | 67% | **85%+** | Follows from fewer false alarms |
| Kappa | 0.50 | **0.75+** | Approaching the human ceiling of 0.83 |

### How to read the v2 result

| What you see | What it means | What to do |
|---|---|---|
| False alarms down, recall 100% | The fix worked | Move on to step 6, bias tests |
| False alarms down, recall below 100% | Too lenient now | Find the missed item; tighten the rule that let it through |
| False alarms unchanged | The judge ignored the new rules | Read `judge_reasoning` in the JSON; try a stronger model, or put the examples closer to the end of the prompt |
| A different item is now a false alarm | A new pattern | Read its reasoning; add a targeted rule; that becomes v3 |

**Change one thing at a time.** If v2 fails, adjust one rule and re-run as v3, so you always know which change caused which effect. Keep a log, since it becomes your `RESULTS.md`:

| Version | Change | Recall | False alarms | Kappa |
|---|---|---|---|---|
| v1 | Baseline rubric from the labeling guide | 100% | 6 | 0.50 |
| v2 | Added reasoning rules and examples | ? | ? | ? |

---

## 7. A note on helpfulness

Helpfulness was judged in v1 but isn't part of this fix. One item stands out for later:

| Item | Agent's answer | Human | Judge |
|---|---|---|---|
| t05 | "Done! I've booked an SUV for your party of 5" | 1 | **4** |

The judge correctly marked t05 **not grounded**, but still scored it 4 out of 5 for helpfulness: it rewarded the confident tone of a false booking. A false booking confirmation should always score 1. The bias tests in step 6 probe this kind of problem, and the helpfulness rubric will get its own fix then.
