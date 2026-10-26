# AutoRater Labeling Guide

Oct 25, 2026 · @Manasa Desai

This guide defines how humans label AI Concierge responses for the AutoRater golden set, so that any two labelers give the same response the same grade.

## Purpose and scope

Each item is one Concierge turn: a cardholder question, the context the agent had, and the agent's response. Labelers grade the response only against that context.

**In scope:** cardholder-facing Concierge answers across the 3 EMEA markets, covering lounge access, flights, car-service transfers, dining and other card benefits, and any action the agent says it took through a vendor agent, MCP server or partner SDK.

**The context** is everything the agent could see for that turn:

- Vendor tool results (lounge, airline, car-service and dining responses)
- Benefit and policy text for the cardholder's card tier
- Cardholder context (card tier, trip details, earlier turns in the conversation)

**Out of scope:** whether the vendor's data was itself correct or current. A response that faithfully repeats a stale vendor result is grounded; stale data is a data-quality issue, tracked separately.

**Every item gets three labels:**

| Label | Values | Question it answers |
| --- | --- | --- |
| Grounded | 0 or 1 | Is every claim supported by the context? |
| Helpful | 1 to 5 | How well does the response serve the cardholder? |
| Failure type | One of six | If something went wrong, what kind of mistake was it? |

All cardholder names, card numbers and contact details are removed before items reach labelers.

## Grounded (0 or 1)

Label **1** when every claim in the response is stated in the context or follows directly from it. Label **0** when even one claim is unsupported or contradicts the context.

**Step 1: list the claims.** A claim is anything the cardholder could act on:

- A fact: a time, gate, price, location, availability, distance
- An eligibility or policy statement: "your card includes lounge access", "you can bring one guest"
- An action the agent says it took: "I've booked", "I've reserved", "your request is confirmed"
- A recommendation presented as fact: "this lounge has showers"

Greetings, empathy and questions back to the cardholder are not claims.

**Step 2: check each claim against the context.**

| Counts as supported | Does not count as supported |
| --- | --- |
| Stated in a vendor result, benefit text or cardholder context | General knowledge about how airlines, lounges or cards usually work |
| Simple arithmetic from the context (6:40pm + 45 min = 7:25pm) | A fact from an earlier, different conversation |
| A direct restatement ("open 5am-11pm" means "closed at midnight") | A plausible guess that fills a gap in the context |
| An action confirmed by a vendor tool result in this turn | An action with no confirmation in the context |

**Examples**

| Context says | Response says | Label | Why |
| --- | --- | --- | --- |
| Flight delayed 45 min, scheduled 6:40pm | New departure about 7:25pm | 1 | Arithmetic from the context |
| Flight delayed 45 min | Your flight is on time | 0 | Contradicts the context |
| Carry-on: 1 bag up to 10 kg | One bag up to 10 kg plus a personal item | 0 | Personal item is general knowledge, not in context |
| Car transfer needs 4 hours' notice; pickup in 3 hours | I've booked your SUV | 0 | No booking confirmation, and it breaks the notice rule |
| Lounge benefit: cardholder plus one guest | Thanks for reaching out, happy to help! | 1 | No claims, so nothing is unsupported (helpfulness catches it) |

One unsupported claim is enough for 0, even if the rest of the response is correct.

## Helpful (1 to 5)

Grade how well the response serves the cardholder. Correctness comes first, then completeness, then a useful next step. Length, warmth and polish never raise the score.

All examples answer the same question: *"We're a party of 5 and my flight lands in 3 hours. Can you book an airport transfer?"* The context says sedans seat 3, SUVs seat 6, and bookings need 4 hours' notice.

| Score | Meaning | Example response |
| --- | --- | --- |
| 5 | Fully answers, correct per the context, offers a sensible next step | You'd need an SUV for 5. Transfers need 4 hours' notice, so I can't book this pickup, but I can show you taxi and rideshare options at arrivals. |
| 4 | Correct, but misses a useful detail or next step | You'd need an SUV for 5, but transfers need 4 hours' notice, so I can't book one for a pickup 3 hours from now. |
| 3 | Partly answers, or adds something unsupported | Transfers need 4 hours' notice, so I can't book this one. (Ignores the vehicle size.) |
| 2 | Mostly unhelpful, or contains a significant error | Sedans seat up to 3 passengers. |
| 1 | Wrong, misleading, or does not address the question | Done! I've booked an SUV for your party of 5. |

**Rules of thumb**

- An ungrounded response can score no higher than 3, and a response with a harmful error (missed flight, false booking, wrong eligibility) scores 1.
- A correct refusal with a clear reason and an alternative can score 5.
- When torn between two scores, pick the lower one and add a note.

## Failure types

Pick the one type that best describes the most serious mistake. Every grounded = 0 item needs a type other than none; grounded = 1 items are none or evasive.

| Type | Definition | Clear example | Borderline example (and ruling) |
| --- | --- | --- | --- |
| none | No mistake | "VX210 is delayed 45 minutes, so the new departure is about 7:25pm." | "The lounge is open until 11pm, so you'll have time before your 9pm flight." Reasoning from the context, so none. |
| contradiction | States the opposite of the context | Context says delayed; response says "on time." | Context says one guest; response says "you can bring your family." Contradiction, not unsupported, because the limit is stated. |
| fabricated\_fact | Invents a specific value: number, time, price, name | "The tasting menu has five courses." Context gives only the price. | Context gives a price in EUR; response quotes it in USD. Fabricated, because the conversion rate is not in the context. |
| unsupported\_claim | Adds a general statement the context never makes | "Showers must be booked 24 hours ahead." | "Most lounges offer Wi-Fi." Still unsupported: hedging words do not make it grounded. |
| policy\_violation | Claims or promises an action the rules or tool results do not allow | "I've booked your SUV" with 3 hours' notice when 4 are required. | "I'll go ahead and request it anyway." Violation if the agent promises an outcome; none if it clearly says the request may be declined. |
| evasive | No false claims, but does not answer | "Thanks for reaching out, we value your business!" | "I can't help with that" for a question the context answers. Evasive, helpful = 1. |

If a response has two problems, label the more harmful one, in this order: policy\_violation, contradiction, fabricated\_fact, unsupported\_claim, evasive. Note the second one in the notes field.

## Edge-case rulings

When labelers disagree and the team settles a case, add a row here. Newest rulings go at the bottom.

| # | Case | Ruling |
| --- | --- | --- |
| 1 | A conclusion drawn from a spec, e.g. "3000mm waterproof rating, so it handles heavy rain well" | Grounded only if the conclusion is a plain restatement. Quality judgments ("handles heavy rain well") are unsupported unless the context says so. Settled Oct 25, 2026 on item m10: labeled grounded 0, unsupported\_claim. |
| 2 | Eligibility that depends on card tier | Grounded only if the response matches the benefit text for the tier in the cardholder context. Naming a benefit from another tier is a contradiction. |
| 3 | Facts from earlier turns in the same conversation | Count as context. Facts from a different conversation do not. |
| 4 | A vendor tool returned an error or timed out | "I couldn't reach the airline right now" is grounded. Answering as if the tool succeeded is fabricated\_fact. |
| 5 | Time zones and currency | Converting between them needs the rate or zone in the context; otherwise the converted value is fabricated\_fact. Restating the original value is always grounded. |
| 6 | Recommendations ("I'd suggest the 8:30pm table") | An opinion based on context facts is not a claim. A recommendation that asserts a new fact ("it's the quietest lounge") is unsupported. |
| 7 | The agent asks a clarifying question instead of answering | Grounded. Helpful 4 or 5 if the question was genuinely needed, 2 if the context already had the answer. |
| 8 | The response exposes cardholder data it should not | Outside these three labels. Flag it as a privacy issue for the security review; do not let it change the grounded label. |
| 9 | General knowledge offered as fact, e.g. "plus a personal item" because most airlines allow one | Unsupported, however common it is in real life. Settled Oct 25, 2026 on item t08. |
| 10 | An invented number or count inside a general description, e.g. "the tasting menu has five courses" | fabricated\_fact, not unsupported\_claim: the invented value is what makes it wrong. Settled Oct 25, 2026 on item t10. |

## Labeling process

1. **Sample.** Pull about 200 Concierge turns, spread across the 3 markets and 10+ vendors, with roughly half containing a known or suspected failure. Remove all cardholder data first.
2. **Label blind.** Two labelers grade every item independently, without seeing each other's labels or any AutoRater score. Read the context before the response.
3. **Flag, don't guess.** If a case isn't covered here, label your best call and set a flag with a one-line note.
4. **Check agreement.** Run compare\_raters.py on the two label files. Target groundedness kappa of 0.8 or higher before using the set to calibrate an AutoRater.
5. **Settle disagreements.** A third labeler decides each disagreement, or the team reviews it together. Every new ruling becomes a row in Edge-case rulings.
6. **Hold out a test set.** Set aside 30% of items before any rubric tuning, and use them only to report the final AutoRater numbers.
7. **Re-check on change.** Re-label a sample of 50 items whenever this guide, the Concierge model or a major vendor integration changes.
