"""Judge rubrics. Edit these to calibrate: this is the main lever you tune."""

GROUNDEDNESS_V1 = """You are a strict evaluator for a customer-facing AI agent.

Decide whether the AGENT RESPONSE is fully grounded in the CONTEXT.
- Grounded (1): every factual claim in the response is stated in, or directly follows from, the context.
  A response that makes no factual claims at all counts as grounded.
- Not grounded (0): the response states any fact, number, policy, or completed action that the context
  does not support, or that contradicts the context.

CONTEXT:
{context}

USER QUERY:
{query}

AGENT RESPONSE:
{response}

Think step by step: list each factual claim, then check it against the context.
Return ONLY JSON: {{"claims": ["..."], "reasoning": "...", "grounded": 0 or 1}}"""

HELPFULNESS_V1 = """You are evaluating a customer-facing AI agent.

Rate how well the AGENT RESPONSE helps the user, on a 1-5 scale:
5 = fully answers the query, correct per the context, offers a sensible next step if useful
4 = answers correctly but misses a useful detail or next step
3 = partially answers, or answers with an unsupported addition
2 = mostly unhelpful or contains a significant error
1 = wrong, misleading, or does not address the query

Correctness against the CONTEXT matters more than tone or length. Do not reward length.

CONTEXT:
{context}

USER QUERY:
{query}

AGENT RESPONSE:
{response}

Return ONLY JSON: {{"reasoning": "...", "helpful": 1-5}}"""

PAIRWISE_V1 = """You are comparing two responses from a customer-facing AI agent.

CONTEXT:
{context}

USER QUERY:
{query}

RESPONSE A:
{a}

RESPONSE B:
{b}

Which response is better: more correct per the context, then more helpful? Ignore length and style.
Return ONLY JSON: {{"reasoning": "...", "winner": "A" or "B"}}"""

RUBRICS = {
    "groundedness": GROUNDEDNESS_V1,
    "helpfulness": HELPFULNESS_V1,
    "pairwise": PAIRWISE_V1,
}
