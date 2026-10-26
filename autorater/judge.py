"""AutoRater judge: calls an LLM (via LiteLLM) or a deterministic mock, with on-disk caching."""
import hashlib
import json
import os
import re

from .rubrics import RUBRICS

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "cache")


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Judge returned no JSON: {text[:200]}")
    return json.loads(match.group(0))


def call_llm(prompt: str, model: str, temperature: float = 0.0) -> str:
    from litellm import completion  # imported lazily so mock mode needs no deps

    kwargs = {}
    if model.startswith(("ollama/", "ollama_chat/")):
        # Ollama in Docker or on another host: export OLLAMA_API_BASE=http://<host>:11434
        kwargs["api_base"] = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
    resp = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        **kwargs,
    )
    return resp.choices[0].message.content


# ---------- mock judge: lets you test the pipeline with no API key ----------
_FACT = re.compile(r"\$?\d+(?:[.:]\d+)?\s*(?:%|kg|mm|am|pm|days?|hours?)?", re.I)


def _mock(dimension: str, item: dict, a: str = "", b: str = "") -> dict:
    ctx = item["context"].lower()
    if dimension == "pairwise":
        # Deliberately biased toward the longer answer, so the bias test has something to catch.
        return {"reasoning": "mock", "winner": "A" if len(a) >= len(b) else "B"}
    resp = item["response"]
    facts = [f.strip().lower() for f in _FACT.findall(resp) if f.strip()]
    unsupported = [f for f in facts if f not in ctx]
    grounded = 0 if unsupported else 1
    if dimension == "groundedness":
        return {"claims": facts, "reasoning": f"mock; unsupported={unsupported}", "grounded": grounded}
    # Mock helpfulness: rewards length (a known judge bias) and grounding.
    score = 2 + min(len(resp) // 60, 2) + grounded
    return {"reasoning": "mock", "helpful": max(1, min(5, score))}


def judge(dimension: str, item: dict, model: str, rubric: str | None = None, **extra) -> dict:
    """Score one item on one dimension. `rubric` overrides the default prompt template."""
    template = rubric or RUBRICS[dimension]
    prompt = template.format(
        context=item["context"], query=item["query"], response=item.get("response", ""), **extra
    )
    if model == "mock":
        return _mock(dimension, item, extra.get("a", ""), extra.get("b", ""))

    path = _cache_path(model + "\n" + prompt)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    result = _parse_json(call_llm(prompt, model))
    with open(path, "w") as f:
        json.dump(result, f)
    return result
