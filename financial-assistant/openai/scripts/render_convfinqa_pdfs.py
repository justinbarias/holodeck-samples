"""Render every ConvFinQA document into a single combined PDF.

Output structure (after reorganisation):
    H1  Company name (TICKER)         ← one page-break before each company
        H2  Year                      ← grouped chronologically inside the company
            H3  Document ID: <id>     ← canonical doc rendering
                <pre_text>
                <table as a grid>
                <post_text>

The `dialogue` field on each doc is intentionally ignored. Tickers are
mapped to companies via a static table (`TICKER_TO_COMPANY`); unmapped
tickers fall back to the raw ticker string.

Usage:
    python scripts/render_convfinqa_pdfs.py \
        --source data/convfinqa_dataset.json \
        --out    data/convfinqa-source.pdf \
        --splits train,dev \
        --max-per-ticker 5     # optional cap per company for smoke tests
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)


# --- bookmarked doc template ------------------------------------------------
# Heading detectors (HoloDeck's `pdf_processor/heading_extractor.py`, markitdown,
# pymupdf, etc.) prefer PDF outline entries over font-size analysis. We hook
# `afterFlowable` to emit one bookmark + outline entry per heading paragraph,
# keyed off the style name → outline level mapping.

_OUTLINE_LEVELS: dict[str, int] = {"Company": 0, "Year": 1, "DocId": 2}


class BookmarkedDocTemplate(BaseDocTemplate):
    """SimpleDocTemplate-equivalent that emits PDF outline entries for every
    heading paragraph (style names ``Company`` / ``Year`` / ``DocId``)."""

    def __init__(self, filename: str, **kwargs: Any) -> None:
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates([PageTemplate(id="default", frames=[frame])])
        self._bookmark_counter = 0

    def afterFlowable(self, flowable: Any) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = getattr(flowable.style, "name", None)
        level = _OUTLINE_LEVELS.get(style_name)
        if level is None:
            return
        text = flowable.getPlainText()
        self._bookmark_counter += 1
        key = f"bm-{self._bookmark_counter}"
        self.canv.bookmarkPage(key)
        # closed=True collapses children by default — keeps the 3,400-entry
        # outline tree usable in viewers without affecting heading detectors.
        self.canv.addOutlineEntry(text, key, level=level, closed=level < 2)

# --- ticker → company name (shared across the ConvFinQA sample scripts;
# see scripts/_tickers.py for the canonical 133-entry mapping). -------------

from _tickers import TICKER_TO_COMPANY  # noqa: E402

_ID_PATTERN = re.compile(r"^(?:Single|Double)_([A-Z0-9.]+)/(\d{4})/")


# --- styles -----------------------------------------------------------------

_BASE = getSampleStyleSheet()

H1_STYLE = ParagraphStyle(
    "Company",
    parent=_BASE["Heading1"],
    fontSize=20,
    leading=24,
    spaceBefore=0,
    spaceAfter=14,
    textColor=colors.HexColor("#0d2c54"),
)
H2_STYLE = ParagraphStyle(
    "Year",
    parent=_BASE["Heading2"],
    fontSize=15,
    leading=18,
    spaceBefore=14,
    spaceAfter=8,
    textColor=colors.HexColor("#1a4480"),
)
H3_STYLE = ParagraphStyle(
    "DocId",
    parent=_BASE["Heading3"],
    fontSize=11,
    leading=14,
    spaceBefore=10,
    spaceAfter=6,
    textColor=colors.HexColor("#1a1a1a"),
)
BODY_STYLE = ParagraphStyle(
    "Body",
    parent=_BASE["BodyText"],
    fontSize=10,
    leading=13,
    spaceAfter=10,
)
# Monospace style used for tables. We render every table as a GFM pipe-table
# inside a Preformatted block so pdfminer (and any other text extractor that
# walks the PDF line-by-line) emits one text line per row, preserving column
# alignment. Font size is computed per-table to fit the widest row in the
# frame; the dataclass defaults are tuned for the common ConvFinQA shape.
_MONO_FONT = "Courier"
_MONO_CHAR_WIDTH_RATIO = 0.6  # Courier glyphs are ~0.6 * fontSize wide
_MONO_MAX_FONT = 8.0
_MONO_MIN_FONT = 5.0


def _format_number(value: Any) -> str:
    """Render a numeric cell value as a human-readable string.

    Ints get thousands separators; floats keep up to 4 decimals with trailing
    zeros stripped. Anything non-numeric (and non-None) is returned as ``str``.
    Returns the empty string for ``None``.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def _sanitize_cell(text: str) -> str:
    """Make a cell safe for pipe-table rendering: strip pipes and newlines."""
    return text.replace("|", "/").replace("\n", " ").replace("\r", " ").strip()


def _format_pipe_table(table: dict[str, dict[str, Any]]) -> tuple[str, int] | None:
    """Build a GFM pipe-table string from a ConvFinQA column-major table.

    Returns ``(text, max_line_chars)`` or ``None`` if the table is empty.
    Columns are padded to the widest cell so the rendered PDF looks tabular,
    but the markdown is valid GFM regardless of padding.
    """
    columns = list(table.keys())
    if not columns:
        return None
    first_inner = table[columns[0]]
    if not isinstance(first_inner, dict) or not first_inner:
        return None
    rows = list(first_inner.keys())

    header = [""] + [_sanitize_cell(str(c)) for c in columns]
    body: list[list[str]] = []
    for row_label in rows:
        row = [_sanitize_cell(str(row_label))]
        for col in columns:
            inner = table.get(col, {})
            value = inner.get(row_label) if isinstance(inner, dict) else None
            row.append(_sanitize_cell(_format_number(value)))
        body.append(row)

    all_rows = [header] + body
    widths = [max(len(r[i]) for r in all_rows) for i in range(len(header))]

    def _fmt(cells: list[str]) -> str:
        padded = (cell.ljust(widths[i]) for i, cell in enumerate(cells))
        return "| " + " | ".join(padded) + " |"

    sep_cells = ["-" * w for w in widths]
    lines = [_fmt(header), _fmt(sep_cells), *(_fmt(r) for r in body)]
    text = "\n".join(lines)
    return text, max(len(line) for line in lines)


def _build_table(table: dict[str, dict[str, Any]]) -> Preformatted | Paragraph:
    """Render a ConvFinQA `table` dict as a monospace pipe-table flowable.

    The dataset is consistently column-major: outer keys are column headers
    (e.g. years), inner keys are the row labels (e.g. metric names). Inner
    key sets are uniform across columns within a doc (verified across all
    3458 rows of the dataset), so we use the first column's keys as the
    canonical row order.

    Tables are rendered with reportlab's :class:`Preformatted` flowable in
    Courier so pdfminer extracts each table row as a single ``LTTextLine`` —
    downstream callers get valid GFM markdown out of the box.
    """
    if not isinstance(table, dict) or not table:
        return Paragraph("<i>(no table data)</i>", BODY_STYLE)

    built = _format_pipe_table(table)
    if built is None:
        return Paragraph("<i>(no table data)</i>", BODY_STYLE)
    text, max_line_chars = built

    # Pick the largest font size (<= _MONO_MAX_FONT) at which the widest row
    # still fits the printable frame. Falls through to _MONO_MIN_FONT if even
    # the smallest font overflows — very wide tables clip rather than wrap.
    frame_width_pt = LETTER[0] - 1.5 * inch
    fitted = frame_width_pt / (_MONO_CHAR_WIDTH_RATIO * max(max_line_chars, 1))
    font_size = max(_MONO_MIN_FONT, min(_MONO_MAX_FONT, fitted))

    style = ParagraphStyle(
        f"MonoTable_{font_size:.2f}",
        parent=_BASE["Code"],
        fontName=_MONO_FONT,
        fontSize=font_size,
        leading=font_size * 1.2,
        spaceBefore=4,
        spaceAfter=8,
        textColor=colors.HexColor("#1a1a1a"),
    )
    return Preformatted(text, style)


def _doc_section(doc_id: str, doc: dict[str, Any]) -> list[Any]:
    """Compose flowables for a single doc: H3 + pre/table/post."""
    pre_text = doc.get("pre_text") or ""
    post_text = doc.get("post_text") or ""
    table = doc.get("table") or {}

    flowables: list[Any] = [
        Paragraph(f"Document ID: {escape(doc_id)}", H3_STYLE),
    ]
    if pre_text:
        flowables.append(Paragraph(escape(pre_text), BODY_STYLE))
    flowables.append(KeepTogether([_build_table(table), Spacer(1, 8)]))
    if post_text:
        flowables.append(Paragraph(escape(post_text), BODY_STYLE))
    return flowables


def _parse_ticker_year(doc_id: str) -> tuple[str, str] | None:
    m = _ID_PATTERN.match(doc_id)
    if not m:
        return None
    return m.group(1), m.group(2)


def _company_label(ticker: str) -> str:
    """Render the H1 label for a ticker — `Company Name (TICKER)` if known,
    otherwise just `TICKER`."""
    name = TICKER_TO_COMPANY.get(ticker)
    return f"{name} ({ticker})" if name else ticker


def _iter_split(payload: dict[str, Any], split: str) -> list[dict[str, Any]]:
    items = payload.get(split)
    if not isinstance(items, list):
        raise SystemExit(f"split {split!r} not found or not a list in source dataset")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to convfinqa_dataset.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/convfinqa-source.pdf"),
        help="Output PDF path (default: data/convfinqa-source.pdf)",
    )
    parser.add_argument(
        "--splits",
        default="train,dev",
        help="Comma-separated splits to include (default: train,dev)",
    )
    parser.add_argument(
        "--max-per-ticker",
        type=int,
        default=None,
        help="Cap the number of docs rendered per ticker (smoke tests). "
        "Docs are ordered by (year, doc_id) and the first N are kept.",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"source not found: {args.source}")

    payload = json.loads(args.source.read_text())
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    # Group: ticker -> year -> [(doc_id, doc), ...]
    grouped: dict[str, dict[str, list[tuple[str, dict[str, Any]]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    skipped_unparseable = 0
    for split in splits:
        for item in _iter_split(payload, split):
            doc_id = item.get("id")
            doc = item.get("doc")
            if not doc_id or not isinstance(doc, dict):
                skipped_unparseable += 1
                continue
            parsed = _parse_ticker_year(doc_id)
            if parsed is None:
                skipped_unparseable += 1
                continue
            ticker, year = parsed
            grouped[ticker][year].append((doc_id, doc))

    if args.max_per_ticker is not None:
        if args.max_per_ticker < 0:
            raise SystemExit("--max-per-ticker must be >= 0")
        for ticker in list(grouped.keys()):
            flat = sorted(
                (
                    (year, doc_id, doc)
                    for year, docs in grouped[ticker].items()
                    for doc_id, doc in docs
                ),
                key=lambda t: (t[0], t[1]),
            )[: args.max_per_ticker]
            trimmed: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
            for year, doc_id, doc in flat:
                trimmed[year].append((doc_id, doc))
            if trimmed:
                grouped[ticker] = trimmed
            else:
                del grouped[ticker]

    # Stable ordering: companies by (company_name, ticker); years ascending;
    # docs by id within a year.
    sorted_tickers = sorted(
        grouped.keys(), key=lambda t: (TICKER_TO_COMPANY.get(t, t).lower(), t)
    )

    story: list[Any] = []
    rendered = 0
    unmapped: set[str] = set()
    for idx, ticker in enumerate(sorted_tickers):
        if ticker not in TICKER_TO_COMPANY:
            unmapped.add(ticker)
        if idx > 0:
            story.append(PageBreak())
        story.append(Paragraph(escape(_company_label(ticker)), H1_STYLE))
        for year in sorted(grouped[ticker].keys()):
            story.append(Paragraph(escape(year), H2_STYLE))
            for doc_id, doc in sorted(grouped[ticker][year], key=lambda p: p[0]):
                story.extend(_doc_section(doc_id, doc))
                rendered += 1

    if not story:
        raise SystemExit("no documents to render")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pdf = BookmarkedDocTemplate(
        str(args.out),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="ConvFinQA documents",
    )
    print(
        f"writing {rendered} docs across {len(sorted_tickers)} companies to "
        f"{args.out} ..."
    )
    pdf.build(story)
    size_kb = args.out.stat().st_size / 1024
    print(
        f"done. companies={len(sorted_tickers)}, docs={rendered}, "
        f"unparseable_ids={skipped_unparseable}, "
        f"unmapped_tickers={len(unmapped)}, size={size_kb:.1f} KB at {args.out}"
    )
    if unmapped:
        print(f"  unmapped tickers (rendered as bare ticker): {sorted(unmapped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
