"""Function tools for the ConvFinQA financial-assistant sample.

Two pure-Python arithmetic helpers — ``subtract`` and ``divide`` — wired into
``agent.yaml`` as ``type: function`` tools. All inputs are strings (that's
what the model actually passes across the JSON tool-call boundary) and both
return strings; we cast to ``float`` internally. Docstrings double as the
tool descriptions presented to the model.

The filing itself is rendered into the first turn's input (see
``scripts/convert_convfinqa.py``), so the agent reads numeric values
directly from context and only needs these tools for arithmetic.
"""

from __future__ import annotations


def _to_float(name: str, value: str) -> float:
    """Parse a model-supplied string argument to ``float``.

    Strips commas, underscores, and whitespace before converting so the
    model can pass values like ``"1,234.56"`` or ``"206_588"`` without
    failing. Raises ``ValueError`` with the argument name if parsing fails.
    """
    cleaned = str(value).replace(",", "").replace("_", "").strip()
    try:
        return float(cleaned)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"argument {name!r} must be a numeric string, got {value!r}"
        ) from exc


def subtract(a: str, b: str) -> str:
    """Compute ``a - b`` for two numeric string operands.

    Args:
        a: Minuend as a numeric string (e.g. ``"206588"`` or ``"1,234.56"``).
        b: Subtrahend as a numeric string.

    Returns:
        The difference ``a - b`` as a string.
    """
    return str(_to_float("a", a) - _to_float("b", b))


def divide(a: str, b: str) -> str:
    """Compute ``a / b`` for two numeric string operands.

    Args:
        a: Dividend as a numeric string.
        b: Divisor as a numeric string; must be non-zero.

    Returns:
        The quotient ``a / b`` as a string.

    Raises:
        ZeroDivisionError: If ``b`` parses to zero.
    """
    denominator = _to_float("b", b)
    if denominator == 0:
        raise ZeroDivisionError("divide: denominator must be non-zero")
    return str(_to_float("a", a) / denominator)
