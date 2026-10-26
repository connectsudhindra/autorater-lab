# AutoRater Lab

A hands-on kit for building and **calibrating** an LLM-based AutoRater (LLM-as-judge) for a customer-facing commerce and travel concierge agent. You define what "good" means, build human-labeled ground truth, check that humans agree, then measure how well a judge model agrees with those humans, fix its rubric, and test it for known judge biases.

## The workflow

| Step | What you do | Tool | Output |
|---|---|---|---|
| 0. Define the labeling guide | Write the rules humans grade by | `docs/LABELING_GUIDE.md` | The guide |
| 1. Build the golden set | Collect conversations; humans label them | `generate_synthetic.py`, `label.py`, `merge_labels.py` | `data/golden*.jsonl` |
| 2. Check human agreement | Two people label blind; compare | `label.py`, `compare_raters.py` | Human-vs-human kappa, disagreements |
| 3. Write the AutoRater rubric | Turn the guide into a judge prompt | `prompts/`, `autorater/rubrics.py` | `groundedness_v1.txt` |
| 4. Run and calibrate | Judge the golden set; compare to humans | `calibrate.py` | Kappa, hallucination recall, disagreements |
| 5. Read the misses and fix | Judge wrong, label wrong, or rubric unclear? | `prompts/*_v2.txt` | A better kappa |
| 6. Test for bias | Verbosity, position, length-over-correctness | `bias_tests.py` | Bias report |
| 7. Confirm on held-out items | Score the final rubric on the test split | `calibrate.py --golden data/golden_test.jsonl` | The number you report |
| 8. Use it as a gate | Block releases below threshold; re-calibrate on model changes | Your CI | A production AutoRater |

## What's here

| File | What it does |
|---|---|
| `docs/LABELING_GUIDE.md` | Definitions, scales, failure types, edge-case rulings and process for human labelers |
| `data/golden.jsonl` | 24 labeled starter items (merchant and travel) with planted mistakes |
| `generate_synthetic.py` | Generates more Concierge candidates (flights, lounges, transfers) with planted failures, using Faker if installed |
| `label.py` | Blind labeling in the terminal: shows items without labels, records yours, resumes where you stopped |
| `compare_raters.py` | Human-vs-human agreement, with each disagreement listed |
| `merge_labels.py` | Merges labels into candidates and splits into dev (tune) and test (report) sets |
| `autorater/rubrics.py` | Judge prompts for groundedness, helpfulness and pairwise comparison |
| `autorater/judge.py` | Calls any model through LiteLLM (Ollama, Anthropic, OpenAI, Gemini) with caching, or a `mock` judge |
| `autorater/metrics.py` | Cohen's kappa, quadratic-weighted kappa, Spearman, hallucination precision/recall |
| `calibrate.py` | Runs the judge on a golden file and writes a report with every disagreement |
| `bias_tests.py` | Verbosity bias, position bias, and "padded wrong answer beats short right answer" |
| `prompts/` | Copies of the v1 rubrics to edit into v2, v3 |

## Setup

```bash
pip install -r requirements.txt
python3 calibrate.py --model mock      # no model needed; checks the pipeline works
python3 bias_tests.py --model mock
```

### Judge models

Any LiteLLM model string works.

**Ollama, native app:**
```bash
ollama pull qwen2.5:7b
python3 calibrate.py --model ollama/qwen2.5:7b --tag v1
```

**Ollama in Docker:** publish port 11434, pull models inside the container, and point the lab at it.
```bash
docker ps                                   # find the container name, e.g. docker-ollama-1
docker exec -it docker-ollama-1 ollama pull qwen2.5:7b
export OLLAMA_API_BASE=http://localhost:11434
python3 calibrate.py --model ollama/qwen2.5:7b --tag v1
```
If the lab itself runs in a container, use `http://host.docker.internal:11434` (Docker Desktop) or the Ollama service name on a shared network.

**Hosted:** set the provider's API key env var, then for example `--model anthropic/claude-haiku-5-5`.

Reports land in `reports/` as `.md` and `.json`. Judge calls are cached in `reports/cache/`, so re-runs are free.

## The mock baseline

The mock judge is deliberately weak: it only checks numbers, and it rewards length. On the starter set it scores groundedness kappa about 0.07, and a padded wrong answer beats a short correct one 5 out of 5 times. That's what an uncalibrated AutoRater looks like.

## Exercises

**1. Check human agreement on the starter set (30 min).** Read `docs/LABELING_GUIDE.md`, then run `python3 label.py` to label all 24 items blind, and `python3 compare_raters.py data/golden.jsonl data/rater2.jsonl`. Settle each disagreement: fix the label or add an edge-case ruling. Item m10 is deliberately borderline and conflicts with ruling 1.

**2. Baseline a real judge (30 min).** Run `calibrate.py` with two models, e.g. `qwen2.5:7b` and `llama3.2`. Record groundedness kappa, hallucination recall and helpfulness weighted kappa.

**3. Read every disagreement (1 hour).** For each: was the judge wrong, the label wrong, or the rubric ambiguous? Check t06 (arithmetic: easy false alarm) and t07 (partly correct: easy miss) first.

**4. Iterate the rubric (2-3 hours).** Copy `prompts/groundedness_v1.txt` to `groundedness_v2.txt` and change one thing at a time, for example:
- Ask for claim-by-claim verification with a quote from the context for each claim
- Add two or three few-shot examples of tricky cases
- State that a completed action ("I've booked...") is a claim needing confirmation in the context
- State that simple arithmetic from the context counts as supported

Keep `{context}`, `{query}` and `{response}` as placeholders, and write literal JSON braces doubled (`{{ }}`), as in v1.

```bash
python3 calibrate.py --model ollama/qwen2.5:7b --groundedness-prompt prompts/groundedness_v2.txt --tag v2
```

**5. Run the bias tests (1 hour).** `python3 bias_tests.py --model <m>`. If padding raises scores, tell the judge not to reward length, with examples. If A/B swaps change the pick, score both orders.

**6. Grow the set and hold out a test split (2 hours).**
```bash
python3 generate_synthetic.py --n 25 --out data/candidates.jsonl
python3 label.py --golden data/candidates.jsonl --out data/candidates_rater1.jsonl
python3 merge_labels.py data/candidates.jsonl data/candidates_rater1.jsonl --holdout 0.3
python3 calibrate.py --golden data/golden_dev.jsonl --model ollama/qwen2.5:7b --tag dev
```
Tune only on `golden_dev.jsonl`. Score `golden_test.jsonl` once, at the end. `planted` is what the generator intended, not a label; review items where your label differs from it.

**7. Simulate a model upgrade (1 hour).** Swap the judge model and re-run on the test split. Did agreement hold? In production you re-calibrate on every judge or product model change.

## Reading the numbers

| Metric | Weak | Usable | Strong |
|---|---|---|---|
| Groundedness kappa | < 0.4 | 0.6-0.8 | > 0.8 |
| Hallucination recall | < 70% | 80-90% | > 90% |
| Helpfulness weighted kappa | < 0.4 | 0.6-0.75 | > 0.75 |

Human-vs-human agreement is the ceiling: an AutoRater can't meaningfully beat it. For a launch gate, **hallucination recall** matters most, because a missed hallucination reaches a customer.

## Synthetic vs real data

Synthetic items are cleaner than real failures, so a judge usually scores higher on them. Use them to practice and to cover rare failure types. For any number you report, use real conversations scrubbed of personal data, and report synthetic and real scores separately.

## Putting it on GitHub

Add a `RESULTS.md` with a table of rubric version x model x split x kappa x recall, plus three or four sentences on what moved the numbers.
