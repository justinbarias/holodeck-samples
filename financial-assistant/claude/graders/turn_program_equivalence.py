"""Illustrative ``type: code`` grader for the ConvFinQA sample.

Checks that the sequence of arithmetic tool calls the agent made on a turn
matches the shape *and* the arguments of ``ctx.turn_config["turn_program"]``.

A ConvFinQA ``turn_program`` is a comma-separated chain like::

    subtract(206588, 181001), divide(#0, 181001)

where each call is ``op(arg0, arg1)`` and each argument is either:

* a numeric literal (e.g. ``206588``),
* a back-reference ``#N`` that resolves to the result of the N-th prior call,
* a ``const_<number>`` sentinel (ConvFinQA uses ``const_100`` for percent
  conversions).

For each expected call we (1) confirm the op name matches, then (2) resolve
the expected argument tokens (substituting prior tool results for ``#N`` and
the literal for ``const_<N>``) and compare them numerically to the
agent-supplied arguments. Mismatches produce a human-readable ``reason``
pointing to the specific op and argument that diverged.
"""

from __future__ import annotations

import math
import re
from typing import Any

from holodeck.lib.test_runner.code_grader import GraderContext, GraderResult

# ``op(`` — matches a call head; we then scan the matching ``)`` to capture
# the arg list, so we handle whitespace-rich programs robustly.
_OP_HEAD_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
# The Claude Agent SDK surfaces HoloDeck function tools as
# ``mcp__holodeck_tools__<name>``; strip any such prefix before matching.
_MCP_PREFIX_RE = re.compile(r"^mcp__[A-Za-z0-9_]+__")
# ConvFinQA constants look like ``const_100`` / ``const_1000``.
_CONST_RE = re.compile(r"^const_(-?\d+(?:\.\d+)?)$")

# Arithmetic ops we care about — non-arithmetic tool calls (retrieval, etc.)
# are ignored so they don't offset the expected/actual alignment.
_ARITHMETIC_OPS = {"subtract", "divide", "add", "multiply"}

# Numeric tolerance for arg comparison — ConvFinQA values are often rounded
# (e.g. ``35.8`` vs ``35.80`` vs a computed ``35.799999999999``).
_REL_TOL = 1e-3
_ABS_TOL = 1e-3


def _parse_program(program: str) -> list[tuple[str, list[str]]]:
    """Parse ``turn_program`` into an ordered list of ``(op, [arg_tokens])``.

    Walks the string, matches each op head, then consumes characters up to
    the next ``)`` to pull out the raw arg substring. Handles a single level
    of parentheses (ConvFinQA programs don't nest).
    """
    calls: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(program):
        m = _OP_HEAD_RE.search(program, i)
        if not m:
            break
        op = m.group(1)
        args_start = m.end()  # just past the opening '('
        close = program.find(")", args_start)
        if close == -1:
            break
        raw = program[args_start:close]
        tokens = [t.strip() for t in raw.split(",") if t.strip()]
        calls.append((op, tokens))
        i = close + 1
    return calls


def _normalize_tool_name(name: str) -> str:
    return _MCP_PREFIX_RE.sub("", name or "")


def _to_float(value: Any) -> float | None:
    """Best-effort numeric cast. Handles strings with commas/underscores."""
    if value is None:
        return None
    if isinstance(value, bool):  # bool is int in Python; exclude it
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    text = str(value).replace(",", "").replace("_", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _resolve_expected_arg(
    token: str, prior_results: list[float | None]
) -> float | None:
    """Resolve a turn_program arg token to a number.

    * ``#N`` → result of the N-th prior (arithmetic) call.
    * ``const_<num>`` → the numeric literal.
    * Otherwise → parse as a number.
    """
    if token.startswith("#"):
        try:
            idx = int(token[1:])
        except ValueError:
            return None
        if 0 <= idx < len(prior_results):
            return prior_results[idx]
        return None
    const_match = _CONST_RE.match(token)
    if const_match:
        try:
            return float(const_match.group(1))
        except ValueError:
            return None
    return _to_float(token)


def _actual_args_ordered(args: dict[str, Any]) -> list[float | None]:
    """Return the invocation's numeric args in deterministic order.

    HoloDeck function tools receive named args, but ConvFinQA's ``turn_program``
    is positional. We order by sorted key name — for the sample's
    ``subtract(a, b)`` / ``divide(a, b)`` tools this matches positional order.
    """
    return [_to_float(args[k]) for k in sorted(args.keys())]


def _floats_equal(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return False
    return math.isclose(a, b, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)


def turn_program_equivalence(ctx: GraderContext) -> GraderResult:
    """Pass when actual tool calls match the ops *and* args of ``turn_program``.

    Returns ``score=1.0`` on exact match (within numeric tolerance), ``0.0``
    otherwise, with a ``reason`` string describing the first divergence.
    """
    program = ctx.turn_config.get("turn_program", "")
    expected = [
        (op, tokens)
        for op, tokens in _parse_program(program)
        if op in _ARITHMETIC_OPS
    ]
    if not expected:
        # No arithmetic ops to verify (e.g. a bare lookup turn like "60.94").
        return GraderResult(
            score=1.0,
            passed=True,
            reason="no arithmetic operations in turn_program; nothing to verify",
        )

    actual = [
        inv
        for inv in ctx.tool_invocations
        if _normalize_tool_name(inv.name) in _ARITHMETIC_OPS
    ]

    if len(actual) != len(expected):
        return GraderResult(
            score=0.0,
            passed=False,
            reason=(
                f"expected {len(expected)} arithmetic call(s) "
                f"{[op for op, _ in expected]}, got {len(actual)} "
                f"{[_normalize_tool_name(inv.name) for inv in actual]}"
            ),
        )

    # Walk expected/actual pairs, resolving #N back-refs against the results
    # of the arithmetic calls we've already verified.
    prior_results: list[float | None] = []
    for i, ((expected_op, arg_tokens), inv) in enumerate(zip(expected, actual)):
        actual_op = _normalize_tool_name(inv.name)
        if actual_op != expected_op:
            return GraderResult(
                score=0.0,
                passed=False,
                reason=(
                    f"op mismatch at position {i}: expected {expected_op!r}, "
                    f"got {actual_op!r}"
                ),
            )
        expected_values = [
            _resolve_expected_arg(t, prior_results) for t in arg_tokens
        ]
        actual_values = _actual_args_ordered(dict(inv.args or {}))
        if len(expected_values) != len(actual_values):
            return GraderResult(
                score=0.0,
                passed=False,
                reason=(
                    f"arg count mismatch at {expected_op!r} "
                    f"(position {i}): expected {len(expected_values)} "
                    f"({arg_tokens}), got {len(actual_values)} "
                    f"({list(inv.args or {})})"
                ),
            )
        for j, (exp, act) in enumerate(zip(expected_values, actual_values)):
            if not _floats_equal(exp, act):
                return GraderResult(
                    score=0.0,
                    passed=False,
                    reason=(
                        f"arg mismatch at {expected_op!r} "
                        f"(position {i}, arg {j}): expected "
                        f"{arg_tokens[j]!r} (resolved {exp}), got "
                        f"{list((inv.args or {}).values())[j] if j < len(inv.args or {}) else None!r} "
                        f"(parsed {act})"
                    ),
                )
        prior_results.append(_to_float(inv.result))

    return GraderResult(
        score=1.0,
        passed=True,
        reason=(
            f"all {len(expected)} arithmetic call(s) matched ops and args: "
            f"{[op for op, _ in expected]}"
        ),
    )
