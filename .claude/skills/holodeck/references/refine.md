# Mode: refine

You're helping a developer turn "the agent kinda works" into "the agent reliably works", using HoloDeck's test-and-evaluate loop. The mental model is the **testing pyramid**: the cheapest, most deterministic graders form the wide base; LLM-as-judge sits at the apex and stays small.

## The pyramid (use it in this order)

```
                       ┌──────────────────────┐
                       │   LLM-as-judge       │   ← deepeval metrics, last resort
                       │  (groundedness etc.) │     slow • costly • non-deterministic
                       ├──────────────────────┤
                       │   Code graders       │   ← custom Python predicates
                       │  (type: code)        │     fast • deterministic • free
                       ├──────────────────────┤
                       │   Standard graders   │   ← numeric, exact_match, contains, regex
                       │  (type: standard)    │     fast • deterministic • free
                       └──────────────────────┘
```

A test case passes the *cheapest* check that can possibly distinguish a right answer from a wrong one. Push as much logic down the pyramid as possible.

**Triage rule:** if you can describe the correctness check in one paragraph of Python, it belongs in a code grader, not deepeval. If you can describe it with a regex or a numeric tolerance, it belongs in a standard grader.

## Standard graders — your default

Use these for ~70-80% of your assertions. They're free, fast, and deterministic.

| Metric | When to use |
|---|---|
| `exact_match` | The agent must emit a specific literal string (e.g. a JSON envelope). |
| `numeric` | The answer is a number; pair with `relative_tolerance` (preferred) or `absolute_tolerance`. Set `accept_percent: true` if the model sometimes emits `33.2%`. |
| `contains` | The output must mention a phrase (e.g. `"escalating to PagerDuty"`). |
| `regex` | The output must match a pattern (e.g. an ISO date). |
| `length` | Output is within a token / char range (rarely useful on its own). |

If the agent returns structured output (`response_format`), grade the leaf with `response_path:`. For example, with `response_format` requiring `{ "answer": <number> }`, the metric block should be:

```yaml
- type: standard
  metric: numeric
  response_path: answer
  relative_tolerance: 0.01
  accept_percent: true
```

## Code graders — your middle layer

When the right-answer check involves *logic* (e.g. "the agent's first tool call's `program` must be equivalent to `divide(a, b)` regardless of variable naming"), write a Python predicate:

```yaml
- type: code
  metric: my-grader-name
  file: graders/my_grader.py
  function: grade            # signature: grade(actual, expected, **kwargs) -> dict
```

The function returns `{"passed": bool, "score": float, "reason": str}`. See `holodeck-samples/financial-assistant/claude/graders/turn_program_equivalence.py` for a working example that parses tool-call programs and checks mathematical equivalence.

Code graders are perfect for:
- **Program equivalence** (tool-call traces, generated SQL, generated code).
- **Structural checks** (the JSON has the right shape; the array has at least N items).
- **Multi-field correctness** (the answer matches AND it cited the right source).
- **Domain-specific tolerance** (e.g. financial answers where `0.05995` and `5.995%` should both count).

The grader is just Python — debug it with `python -c "from graders.my_grader import grade; print(grade(...))"`, then wire it back into the YAML.

## LLM-as-judge — use sparingly

DeepEval metrics (`type: deepeval`, e.g. `groundedness`, `answer_relevancy`, `faithfulness`) are the apex of the pyramid. They're expensive, slow, and non-deterministic. **Use them only when standard + code can't capture the metric.**

Good candidates for deepeval:
- Narrative quality ("does the explanation read like a senior analyst wrote it?")
- Groundedness on free-text answers ("does the response stay within the retrieved context?")
- Open-ended Q&A where there's no single right answer

Bad candidates (use cheaper graders instead):
- Numeric correctness → standard `numeric`
- Specific phrase required → standard `contains`
- Tool-call correctness → code grader
- Output schema → already enforced by `response_format`

Per-metric model config: deepeval metrics can pin a specific judge model:

```yaml
- type: deepeval
  metric: groundedness
  threshold: 0.8
  model:
    provider: openai
    name: gpt-4o-mini   # cheap, fast — fine for most judging
```

A typical agent's eval block is **mostly standard graders, one or two code graders, zero or one deepeval metric**. If you find yourself adding three deepeval metrics, push back — what's the *actual* failure mode you're trying to catch?

## Test cases: where to put them

Two options:

1. **Inline in `agent.yaml`** under `test_cases:` — fine for ≤5 cases or quick sanity checks.
2. **External YAML pointed at by `test_cases_file:`** — preferred for >5 cases or when the cases are generated by a script. Keeps `agent.yaml` readable.

Multi-turn cases use the `turns:` shape:

```yaml
- name: alxn-2007-rental-payments
  turns:
  - input: For ALXN in 2007, what were total rental payments?
    ground_truth: '27141'
    expected_tools: [convfinqa_archive]
    turn_config:
      turn_program: divide(27141, 1)
      expected_document: Single_ALXN/2007/page_104.pdf
```

`expected_tools`, `turn_program`, and `expected_document` are graded by code graders — they're not enforced by the model.

## Running tests

```bash
holodeck test                                  # all cases, parallel per `execution.parallel_test_cases`
holodeck test --test-case <name>               # one case, useful for iterating
holodeck test --test-case <name> --verbose     # full prompt + response + grader trace
```

Slow corpora (large PDFs, big vector stores): expect 1–3 minutes ingest on first run, then sub-second per turn after that. If first-turn timeout fires, raise `execution.file_timeout` (default 180s is conservative).

## Analyzing the results JSON

Results land at `results/<agent>/<timestamp>.json`. Each test case has a `turns[]` array; each turn has `expectations[]` (one per grader). Key fields:

| Field | What it tells you |
|---|---|
| `turns[i].response` | What the agent actually said |
| `turns[i].tool_calls` | The sequence of tool calls in that turn |
| `turns[i].expectations[j].metric` | Which grader fired |
| `turns[i].expectations[j].passed` | Result of that grader |
| `turns[i].expectations[j].score` | Numeric score (when applicable) |
| `turns[i].expectations[j].reason` | Why it passed or failed |
| `turns[i].latency_ms` | Per-turn time |
| `turns[i].token_usage` | Per-turn tokens (input + output) |

**Triage workflow when most tests fail:**

1. `jq '.results[] | select(.turns[].expectations[].passed == false) | .name' results/<file>.json` — list failing cases.
2. Open one failing case, read the `response` and the failed `expectations[].reason`.
3. Decide: is the agent wrong, or is the grader wrong? A grader that's too strict is a common false positive — fix it before re-running.
4. If the agent is wrong, scan for a pattern: same tool always called with bad args? Same kind of question always wrong? Same retrieval result missing?
5. Edit `agent.yaml` (instructions, tool descriptions, retrieval params) — *not* the test cases.
6. Re-run only the failing cases: `holodeck test --test-case <name>`.

**Triage workflow when scores regressed after a change:**

1. `diff` the two JSON files, focusing on `turns[].expectations[].passed`.
2. For each newly-failing turn, compare the old `response` vs new `response`. If the agent's behavior changed, your YAML edit had the side effect you didn't intend.

## Dashboard (background)

The dashboard renders results history with sortable runs, per-case drill-down, and trend lines.

The command is `holodeck test view` (run from the agent's directory). It defaults to `http://127.0.0.1:8501` and would normally try to pop open a browser tab — pass `--no-browser` when starting in the background so it doesn't.

Start it in the background so it doesn't tie up the terminal:

```bash
nohup holodeck test view --no-browser > /tmp/holodeck-dashboard.log 2>&1 &
echo $!   # save the PID so you can kill it later
open http://127.0.0.1:8501
```

To stop it: `kill <PID>` (or `pkill -f "holodeck test view"`).

The dashboard reads from `results/`, so it doesn't need to be running while tests execute. Start it after a run to inspect.

## Adjacent skill: `holodeck.tune`

For tightly scoped score-improvement work on an existing agent, `holodeck.tune` (separate skill) provides a focused tuning loop. Suggest it when the user says things like "the agent is at 73% — get it to 85%" rather than "help me build my eval suite".

## Common refine traps

| Symptom | Cause / fix |
|---|---|
| Every case passes but the agent feels wrong | Graders too lenient. Add a code grader that checks the *reasoning* (tool calls, intermediate scores), not just the final answer. |
| `numeric` grader passes `13.7%` against ground truth `0.05995` | `absolute_tolerance` was too generous. Use `relative_tolerance: 0.01` for ConvFinQA-style answers; the previous defaults were buggy. |
| Deepeval is slow and burns budget | You're using it where a standard grader would do. Audit each deepeval metric — can you describe the check in Python? |
| Grader file isn't found | Run `holodeck test` from the agent's directory so `agent.yaml`'s parent is on `sys.path`. |
| Dashboard shows stale data | The dashboard reads `results/` at request time; refresh the browser. If the file is malformed, the run probably crashed mid-write — check the test runner's stderr. |

## When done with refine

Hand off to `ship` mode when the user has a green or near-green run and starts talking about deployment, scale, or production. Don't push them out of refine prematurely — landing the eval suite is its own deliverable.

## Authoritative references (always fetch fresh)

- `https://docs.useholodeck.ai/guides/evaluations/`
- `https://docs.useholodeck.ai/guides/dashboard/`
- `https://docs.useholodeck.ai/api/evaluators/`
- `https://docs.useholodeck.ai/api/test-runner/`
- DeepEval docs (external): `https://docs.confident-ai.com/`
