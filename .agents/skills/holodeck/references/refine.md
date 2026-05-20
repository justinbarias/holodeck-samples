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

### YAML wiring

```yaml
evaluations:
  metrics:
    - type: code
      grader: "graders.my_grader:grade"   # "module.path:callable" — colon-separated
      threshold: 0.8                      # used when the grader returns a bare float
      enabled: true                       # default true
      fail_on_error: false                # if true, a grader exception fails the whole test case
      name: "tool-program-equivalence"    # optional display name (defaults to the callable name)
```

`grader:` is **one string** of the form `module.path:callable_name` — not the separate `file:` + `function:` fields a `function` *tool* uses. The runner does `importlib.import_module(module_path)` + `getattr(...)` at config-load time, so a bad import path raises `ConfigError` *before* any agent call. That early-fail is intentional — it stops you wasting tokens on a typo'd grader path.

The module is resolved against `agent.yaml`'s directory on `sys.path`. So `grader: "graders.turn_program_equivalence:turn_program_equivalence"` resolves to `graders/turn_program_equivalence.py:def turn_program_equivalence(...)` next to `agent.yaml`.

### Required package import

```python
from holodeck.lib.test_runner.code_grader import GraderContext, GraderResult
from holodeck.models.test_result import ToolInvocation   # only if you type-annotate
```

`holodeck-ai` is the PyPI package — your sample's `pyproject.toml` (or local venv) needs `holodeck-ai` installed. When you run `holodeck test`, the CLI's own venv provides these imports; you only need to add `holodeck-ai` as a dev dependency if you want IDE type-checking on grader files.

### Function signature

```python
def my_grader(ctx: GraderContext) -> bool | float | GraderResult:
    ...
```

One positional arg — the `GraderContext` — and any one of three return shapes (see below).

### What's in the `GraderContext`

Everything the runner knows about the turn that just executed:

| Field | Type | What it carries |
|---|---|---|
| `ctx.turn_input` | `str` | The user prompt for *this* turn (multi-turn: the current user message). |
| `ctx.agent_response` | `str` | The agent's final text response. With `response_format`, this is the raw JSON envelope — parse it inside the grader. |
| `ctx.ground_truth` | `str \| None` | Whatever you wrote under `ground_truth:` in the test case YAML. None if you didn't set one. |
| `ctx.tool_invocations` | `tuple[ToolInvocation, ...]` | Every tool call the agent made on this turn, in order. Read-only (frozen tuple). |
| `ctx.retrieval_context` | `tuple[str, ...] \| None` | Chunks returned by retrieval tools on this turn. Lets you write a *deterministic* groundedness check without invoking an LLM. |
| `ctx.turn_index` | `int` | Zero-based position in the multi-turn dialogue. Use this to skip graders on the first turn, or to require a specific tool only on turn 0. |
| `ctx.test_case_name` | `str \| None` | The `name:` of the test case — useful for richer `reason` strings. |
| `ctx.turn_config` | `dict[str, Any]` | **Free-form dict** from the test case's `turn_config:` block. This is your escape hatch — stash anything the grader needs (`turn_program`, `expected_document`, `expected_schema`, etc.). The runner doesn't interpret any of these keys; the grader reads them directly. |

The dataclass is frozen — `ctx.tool_invocations` and `ctx.retrieval_context` are tuples, not lists, so the grader can't accidentally mutate runner state.

### `ToolInvocation` shape

Each entry in `ctx.tool_invocations`:

```python
inv.name          # str  — tool name (Claude prefixes function tools with mcp__holodeck_tools__)
inv.args          # dict — input parameters as the LLM supplied them
inv.result        # Any  — tool output (scalar / dict / list / str). None if the call raised.
inv.bytes         # int  — len(json.dumps(result)). Useful for "result must be < N KB" checks.
inv.duration_ms   # int | None — None on backends that don't report it (rare).
inv.error         # str | None — error message when the call failed.
```

Note: when an agent runs through the Claude backend, function tools surface with a `mcp__holodeck_tools__` prefix. Strip it before comparing names:

```python
import re
_MCP_PREFIX = re.compile(r"^mcp__[A-Za-z0-9_]+__")
plain = _MCP_PREFIX.sub("", inv.name)
```

### Return shapes (all valid)

```python
# 1. Bare bool — runner treats True as score 1.0 / passed=True.
return ctx.agent_response.strip().startswith("```sql")

# 2. Bare float — runner derives passed from the metric's `threshold:`
#    (or default >= 0.5 if no threshold set).
return overlap_ratio(ctx.retrieval_context, ctx.ground_truth)

# 3. Fully-formed GraderResult — most informative; fills the dashboard.
return GraderResult(
    score=0.0,
    passed=False,
    reason=f"expected tool {expected!r}, got {actual!r}",
    details={"expected_tools": expected, "got_tools": actual},
)
```

`reason` shows up in the dashboard and in `results/<file>.json` next to the failing assertion — make it actionable. `details` is a free-form dict for structured data the dashboard renders in a collapsible panel.

### What you can actually do with a code grader

The base case is "compare a number" — but the access to `tool_invocations`, `retrieval_context`, and `turn_config` opens a much wider range:

- **Tool-call program equivalence.** Compare the actual `(op, args)` sequence against `ctx.turn_config["turn_program"]`. The financial-assistant sample (`graders/turn_program_equivalence.py`) is the reference implementation — handles back-references (`#N`), `const_<n>` sentinels, and numeric tolerance.
- **Expected-document check on retrieval.** When a turn says `turn_config: {expected_document: "filing-X.pdf"}`, walk `ctx.tool_invocations`, find the retrieval call, and assert that the returned chunks include filing X. Catches "right answer for wrong reason" — e.g. the agent guessed without grounding.
- **Deterministic groundedness.** For free-text answers, check that every numeric token in `ctx.agent_response` appears in `ctx.retrieval_context`. Cheap heuristic, catches the common hallucination case without an LLM judge.
- **Structured-output schema.** Parse `ctx.agent_response` as JSON, validate against a `jsonschema` `Draft202012Validator`, return `(score=0/1, reason=validator.errors)`.
- **Generated-code correctness.** Extract a fenced code block from `ctx.agent_response`, exec it in a sandboxed namespace, compare its output to `ctx.ground_truth`. Useful for code-gen agents.
- **Generated-SQL equivalence.** Parse both `ctx.agent_response` and `ctx.ground_truth` with `sqlglot`, normalize, compare AST. Reliable when the agent has freedom in column aliasing / table-ordering.
- **Per-turn tool budget.** Fail if `len(ctx.tool_invocations) > ctx.turn_config["max_tool_calls"]`. Useful when you want to penalise an agent that grinds through retries.
- **Compound assertions.** AND the numeric correctness with the right citation, return a single `GraderResult` with both findings in `details`.

The unifying principle: anything you can describe as a Python function over the turn's I/O can be a code grader. Reach for an LLM judge only when the check genuinely needs natural-language reasoning (style, tone, "is this a good explanation"), not when it's just *tedious* to express in code.

### Wiring the turn-side metadata

The grader reads from `ctx.turn_config`, but you put data *there* in the test case YAML:

```yaml
# data/convfinqa_subset.yaml
- name: ALXN-2007-rental-payments
  turns:
    - input: For ALXN in 2007, what were total rental payments?
      ground_truth: "27141"
      turn_config:
        turn_program: "add(4935, 3144), add(#0, 3160), add(#1, 3200), add(#2, 2768), add(#3, 9934)"
        expected_document: "Single_ALXN/2007/page_104.pdf"
        max_tool_calls: 8
      expected_tools: [convfinqa_archive]
```

Whatever you put under `turn_config:` lands verbatim in `ctx.turn_config` — keys are arbitrary. Treat it like a per-turn dataclass you defined yourself.

### Debug a grader without running the LLM

The grader is pure Python — exercise it directly with a hand-built context:

```python
from holodeck.lib.test_runner.code_grader import GraderContext
from holodeck.models.test_result import ToolInvocation
from graders.my_grader import my_grader

ctx = GraderContext(
    turn_input="what's 2+2?",
    agent_response='{"answer": 4}',
    ground_truth="4",
    tool_invocations=(
        ToolInvocation(name="add", args={"a": "2", "b": "2"}, result="4", bytes=1),
    ),
    retrieval_context=None,
    turn_index=0,
    test_case_name="trivial-add",
    turn_config={"turn_program": "add(2, 2)"},
)
print(my_grader(ctx))
```

Runs in milliseconds, no API key required. Iterate on the grader logic here, *then* wire it back into `agent.yaml`.

See `sample/financial-assistant/claude/graders/turn_program_equivalence.py` for a fully-worked example using `tool_invocations` + `turn_config` together.

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
