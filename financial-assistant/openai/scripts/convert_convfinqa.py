"""Convert upstream ConvFinQA dialogues into HoloDeck multi-turn test cases.

Usage:
    python scripts/convert_convfinqa.py \\
        --source /path/to/convfinqa_dataset.json \\
        --splits train,dev \\
        --max-per-ticker 5 \\
        --out data/convfinqa_subset.yaml

``--splits`` and ``--max-per-ticker`` mirror the same flags in
``render_convfinqa_pdfs.py``. Invoking both scripts with identical values for
these two flags produces bit-identical sets of dialogue IDs, so the YAML test
cases are guaranteed to be a subset of the PDF corpus.

The upstream dataset has shape ``{"train": [...], "dev": [...]}``. Each entry
carries ``id``, ``doc`` (pre_text/post_text/table), and ``dialogue`` with
``conv_questions``, ``conv_answers``, ``turn_program``, and
``executed_answers``. We emit one HoloDeck test case per dialogue — one turn
per ConvFinQA question — with the raw ``turn_program`` string attached under
``turn_config`` so a ``type: code`` grader can read it via
``ctx.turn_config["turn_program"]`` (see
``specs/032-multi-turn-test-cases/contracts/code-grader-contract.md`` §3.1).

The output is a YAML list of test-case dicts, loaded by HoloDeck via the
``test_cases_file:`` pointer in ``agent.yaml`` (commit ``5f0c84a``).

Two input modes:

* **default (``--agent-retrieval`` off)** — the full filing (pre_text + table +
  post_text) is rendered inline as the first turn's ``input``. The agent has
  every fact it needs in context and never has to retrieve.
* **``--agent-retrieval`` on** — the first turn becomes a natural-language
  query referencing the company + filing year (e.g. ``"In Abiomed (ABMD)'s
  2005 annual report, what is the percent change in net cash …"``). No filing
  text is included, so the agent must call the ``convfinqa_archive``
  hierarchical-document tool to retrieve it. Each turn carries
  ``turn_config.expected_document`` = the canonical doc id so a code grader
  can assert which filing was retrieved, and turn 0 carries
  ``expected_tools = ["convfinqa_archive"]`` so the test runner enforces
  that the retrieval call actually happens.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from _tickers import company_label


# Same pattern as scripts/render_convfinqa_pdfs.py — keeps the two scripts
# producing perfectly aligned subsets when invoked with the same cap.
_ID_PATTERN = re.compile(r"^(?:Single|Double)_([A-Z0-9.]+)/(\d{4})/")

# Tool name from agent.yaml — must match the hierarchical_document tool that
# indexes the ConvFinQA archive. Used as the expected_tools entry on turn 0
# of every retrieval-mode test case.
_RETRIEVAL_TOOL_NAME = "convfinqa_archive"


def render_document(doc: dict[str, Any]) -> str:
    """Render a ConvFinQA ``doc`` dict as a compact markdown block.

    The upstream shape is ``{pre_text, post_text, table}`` where ``table`` is
    ``{column: {row: value}}``. We emit the pre-text, then a markdown table
    with columns as headers, then the post-text. This gives the agent the
    full filing excerpt inline — no retrieval needed.
    """
    pre_text = (doc.get("pre_text") or "").strip()
    post_text = (doc.get("post_text") or "").strip()
    table = doc.get("table") or {}

    parts: list[str] = []
    if pre_text:
        parts.append(pre_text)
    if isinstance(table, dict) and table:
        columns = list(table.keys())
        # Collect the union of row keys, preserving first-seen order.
        rows: list[str] = []
        seen: set[str] = set()
        for col in columns:
            col_data = table[col]
            if not isinstance(col_data, dict):
                continue
            for row in col_data:
                if row not in seen:
                    seen.add(row)
                    rows.append(row)
        header = "| metric | " + " | ".join(str(c) for c in columns) + " |"
        sep = "|---" * (len(columns) + 1) + "|"
        lines = [header, sep]
        for row in rows:
            cells = [str(row)]
            for col in columns:
                col_data = table[col]
                value = (
                    col_data.get(row) if isinstance(col_data, dict) else None
                )
                cells.append("" if value is None else str(value))
            lines.append("| " + " | ".join(cells) + " |")
        parts.append("\n".join(lines))
    if post_text:
        parts.append(post_text)
    return "\n\n".join(parts)


def _retrieval_query(question: str, ticker: str, year: str) -> str:
    """Phrase the first-turn question as a natural retrieval query.

    The agent gets the company name + ticker + filing year so it has enough
    signal to call ``convfinqa_archive`` and find the right document. The
    ConvFinQA corpus is drawn from 10-K annual reports, so framing the query
    as "in <Company>'s <year> annual report" matches how a real user would
    ask. Unmapped tickers fall back to bare ticker.
    """
    label = company_label(ticker)
    return f"In {label}'s {year} annual report, {question}"


def dialogue_to_test_case(
    entry: dict[str, Any],
    agent_retrieval: bool = False,
) -> dict[str, Any]:
    """Convert one upstream dialogue dict to a HoloDeck test-case dict.

    Default mode renders the full ConvFinQA document (pre_text + table +
    post_text) as markdown and prepends it to the first turn's ``input`` so
    the agent has the source material inline. Subsequent turns only carry
    the follow-up question — they share the same session and see the
    document in context.

    Retrieval mode (``agent_retrieval=True``) replaces the inline document
    with a natural-language query that names the company + year. The agent
    is forced to call ``convfinqa_archive`` to look the filing up; the
    test runner asserts this via ``expected_tools`` on turn 0, and every
    turn carries ``turn_config.expected_document`` = the canonical doc id
    so a code grader can verify which filing was retrieved.

    Args:
        entry: Upstream ConvFinQA record with ``id``, ``doc``, ``dialogue``.
        agent_retrieval: When True, emit a retrieval-mode test case (see
            module docstring for the full contract).

    Returns:
        A dict shaped as ``{"name": str, "turns": list[dict]}`` that passes
        ``TestCaseModel`` validation.

    Raises:
        KeyError: If the entry is missing required ``dialogue`` fields.
        ValueError: If per-turn arrays are misaligned, or if retrieval mode
            is requested but the entry id cannot be parsed for ticker/year.
    """
    dialogue = entry["dialogue"]
    questions = dialogue["conv_questions"]
    executed = dialogue["executed_answers"]
    programs = dialogue["turn_program"]
    if not (len(questions) == len(executed) == len(programs)):
        raise ValueError(
            f"dialogue arrays misaligned for id={entry.get('id')!r}: "
            f"len(conv_questions)={len(questions)}, "
            f"len(executed_answers)={len(executed)}, "
            f"len(turn_program)={len(programs)}"
        )

    doc_id = entry["id"]
    if agent_retrieval:
        parsed = _parse_ticker_year(doc_id)
        if parsed is None:
            raise ValueError(
                f"retrieval mode requires a parseable id; got {doc_id!r}"
            )
        ticker, year = parsed

    document = render_document(entry.get("doc") or {})
    turns: list[dict[str, Any]] = []
    for i, question in enumerate(questions):
        turn_config: dict[str, Any] = {"turn_program": programs[i]}
        if agent_retrieval:
            # Pin the expected filing on every turn so a code grader can
            # verify the agent retrieved the right document regardless of
            # which turn first triggered the retrieval.
            turn_config["expected_document"] = doc_id

        if i == 0 and agent_retrieval:
            turn: dict[str, Any] = {
                "input": _retrieval_query(question, ticker, year),
                "ground_truth": str(executed[i]),
                # Force the agent to call the hierarchical_document tool on
                # the very first turn; follow-ups can usually be answered
                # from the retrieved context without further lookups.
                "expected_tools": [_RETRIEVAL_TOOL_NAME],
                "turn_config": turn_config,
            }
        elif i == 0 and document:
            turn = {
                "input": (
                    f"Filing excerpt:\n\n{document}\n\n"
                    f"Using the filing above, answer: {question}"
                ),
                "ground_truth": str(executed[i]),
                "turn_config": turn_config,
            }
        else:
            turn = {
                "input": question,
                "ground_truth": str(executed[i]),
                "turn_config": turn_config,
            }
        turns.append(turn)
    return {"name": doc_id, "turns": turns}


def _parse_ticker_year(doc_id: str) -> tuple[str, str] | None:
    """Extract ``(ticker, year)`` from a ConvFinQA ``id`` like
    ``Single_ABMD/2005/page_57.pdf-1``. Returns ``None`` if the id does not
    match the canonical pattern."""
    m = _ID_PATTERN.match(doc_id)
    if not m:
        return None
    return m.group(1), m.group(2)


def _cap_per_ticker(
    entries: list[dict[str, Any]], max_per_ticker: int | None
) -> tuple[list[dict[str, Any]], int]:
    """Group ``entries`` by ticker (parsed from ``id``), sort each ticker's
    dialogues by ``(year, id)``, and keep at most ``max_per_ticker`` per
    ticker. When ``max_per_ticker`` is ``None`` no cap is applied and the
    original order is preserved.

    Returns ``(kept_entries, skipped_unparseable)``. Entries whose ``id`` does
    not match the canonical pattern are dropped (and counted) only when a cap
    is active — without a cap we can't sort or group them anyway, so they are
    passed through untouched.
    """
    if max_per_ticker is None:
        return entries, 0
    if max_per_ticker < 0:
        raise SystemExit("--max-per-ticker must be >= 0")

    grouped: dict[str, list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    skipped_unparseable = 0
    for entry in entries:
        doc_id = entry.get("id")
        if not isinstance(doc_id, str):
            skipped_unparseable += 1
            continue
        parsed = _parse_ticker_year(doc_id)
        if parsed is None:
            skipped_unparseable += 1
            continue
        ticker, year = parsed
        grouped[ticker].append((year, doc_id, entry))

    kept: list[dict[str, Any]] = []
    # Stable per-ticker order: companies alphabetically, dialogues by
    # (year, id) within a ticker — matches render_convfinqa_pdfs.py.
    for ticker in sorted(grouped.keys()):
        per_ticker = sorted(grouped[ticker], key=lambda t: (t[0], t[1]))
        for _year, _doc_id, entry in per_ticker[:max_per_ticker]:
            kept.append(entry)
    return kept, skipped_unparseable


def convert(
    source: Path,
    splits: list[str],
    max_per_ticker: int | None,
    out: Path,
    agent_retrieval: bool = False,
) -> tuple[int, int]:
    """Read upstream JSON, pool the listed splits, cap per ticker if requested,
    write YAML to ``out``.

    Splits are pooled in the order given before grouping/capping — matching
    ``render_convfinqa_pdfs.py`` so the two scripts emit aligned subsets when
    invoked with identical ``--splits`` and ``--max-per-ticker``.

    Args:
        source: Path to ``convfinqa_dataset.json``.
        splits: Splits to pool (e.g. ``["train", "dev"]``).
        max_per_ticker: Per-ticker cap, or ``None`` for no cap.
        out: Output YAML path.
        agent_retrieval: When True, emit retrieval-mode test cases (see
            :func:`dialogue_to_test_case`).

    Returns:
        Tuple of ``(num_written, num_skipped_unparseable)``.
    """
    with source.open("r", encoding="utf-8") as f:
        data = json.load(f)
    pooled: list[dict[str, Any]] = []
    for split in splits:
        if split not in data:
            raise KeyError(
                f"split {split!r} not in dataset (keys: {list(data.keys())})"
            )
        items = data[split]
        if not isinstance(items, list):
            raise SystemExit(f"split {split!r} is not a list in source dataset")
        pooled.extend(items)
    entries, skipped = _cap_per_ticker(pooled, max_per_ticker)
    test_cases = [
        dialogue_to_test_case(e, agent_retrieval=agent_retrieval) for e in entries
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            test_cases,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    return len(test_cases), skipped


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--splits",
        default="train,dev",
        help="Comma-separated splits to include (default: train,dev). "
        "Matches the same flag in render_convfinqa_pdfs.py.",
    )
    parser.add_argument(
        "--max-per-ticker",
        type=int,
        default=None,
        help="Cap the number of dialogues kept per ticker (smoke tests). "
        "Dialogues are ordered by (year, id) across the pooled splits and "
        "the first N are kept. Omit to keep every dialogue.",
    )
    parser.add_argument(
        "--agent-retrieval",
        action="store_true",
        default=False,
        help="Emit retrieval-mode test cases: turn 0 becomes a natural "
        "user query naming the company + year (no inline filing text), "
        "expected_tools is set to require the convfinqa_archive lookup, "
        "and every turn carries turn_config.expected_document with the "
        "canonical doc id for code-grader checks.",
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    if not splits:
        raise SystemExit("--splits must list at least one split")
    count, skipped = convert(
        source=args.source,
        splits=splits,
        max_per_ticker=args.max_per_ticker,
        out=args.out,
        agent_retrieval=args.agent_retrieval,
    )
    msg = f"Converted {count} dialogues → {args.out}"
    if skipped:
        msg += f" (skipped {skipped} entries with unparseable ids)"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
