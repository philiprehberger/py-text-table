"""Render data as clean ASCII/Unicode tables in the terminal with zero configuration."""

from __future__ import annotations

import csv
from typing import Any

__all__ = ["table", "from_dicts", "from_csv"]

_STYLES: dict[str, dict[str, str]] = {
    "unicode": {
        "top_left": "\u250c",
        "top_mid": "\u252c",
        "top_right": "\u2510",
        "mid_left": "\u251c",
        "mid_mid": "\u253c",
        "mid_right": "\u2524",
        "bot_left": "\u2514",
        "bot_mid": "\u2534",
        "bot_right": "\u2518",
        "horizontal": "\u2500",
        "vertical": "\u2502",
        "cross": "\u253c",
    },
    "ascii": {
        "top_left": "+",
        "top_mid": "+",
        "top_right": "+",
        "mid_left": "+",
        "mid_mid": "+",
        "mid_right": "+",
        "bot_left": "+",
        "bot_mid": "+",
        "bot_right": "+",
        "horizontal": "-",
        "vertical": "|",
        "cross": "+",
    },
    "markdown": {
        "top_left": "",
        "top_mid": "",
        "top_right": "",
        "mid_left": "|",
        "mid_mid": "|",
        "mid_right": "|",
        "bot_left": "",
        "bot_mid": "",
        "bot_right": "",
        "horizontal": "-",
        "vertical": "|",
        "cross": "|",
    },
    "minimal": {
        "top_left": "",
        "top_mid": "",
        "top_right": "",
        "mid_left": "",
        "mid_mid": "",
        "mid_right": "",
        "bot_left": "",
        "bot_mid": "",
        "bot_right": "",
        "horizontal": "",
        "vertical": "",
        "cross": "",
    },
    "compact": {
        "top_left": "",
        "top_mid": "",
        "top_right": "",
        "mid_left": "",
        "mid_mid": "+",
        "mid_right": "",
        "bot_left": "",
        "bot_mid": "",
        "bot_right": "",
        "horizontal": "-",
        "vertical": "|",
        "cross": "+",
    },
}


def _is_numeric(value: Any) -> bool:
    """Check if a value is numeric for right-alignment."""
    if isinstance(value, (int, float, complex)) and not isinstance(value, bool):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def _calculate_widths(headers: list[str], rows: list[list[Any]]) -> list[int]:
    """Calculate the maximum width needed for each column."""
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
            else:
                widths.append(len(str(cell)))
    return widths


def _format_cell(value: Any, width: int, align: str) -> str:
    """Pad cell content according to alignment."""
    text = str(value)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def _truncate(value: Any, max_width: int) -> str:
    """Truncate a value to max_width, adding ellipsis if needed."""
    text = str(value)
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3] + "..."


def table(
    headers: list[str],
    rows: list[list[Any]],
    *,
    style: str = "unicode",
    max_width: int | None = None,
) -> str:
    """Render a table string from headers and rows.

    Args:
        headers: Column header strings.
        rows: List of rows, each a list of cell values.
        style: Table style — "unicode", "ascii", "markdown", "minimal", or "compact".
        max_width: Optional maximum width per cell. Cells exceeding this are truncated
            with "..." appended.

    Returns:
        A formatted table string.
    """
    if style not in _STYLES:
        raise ValueError(
            f"Unknown style {style!r}. Choose from: {', '.join(_STYLES)}"
        )

    s = _STYLES[style]

    # Apply truncation if max_width is set
    if max_width is not None:
        headers = [_truncate(h, max_width) for h in headers]
        rows = [[_truncate(cell, max_width) for cell in row] for row in rows]

    widths = _calculate_widths(headers, rows)

    # Determine alignment per column (right for numeric columns)
    col_count = len(headers)
    alignments: list[str] = []
    for col in range(col_count):
        col_values = [row[col] for row in rows if col < len(row)]
        if col_values and all(_is_numeric(v) for v in col_values):
            alignments.append("right")
        else:
            alignments.append("left")

    lines: list[str] = []

    if style == "minimal":
        # Header row
        cells = [
            _format_cell(headers[i], widths[i], alignments[i])
            for i in range(col_count)
        ]
        lines.append("  ".join(cells))
        # Separator
        lines.append("  ".join("-" * w for w in widths))
        # Data rows
        for row in rows:
            cells = [
                _format_cell(row[i] if i < len(row) else "", widths[i], alignments[i])
                for i in range(col_count)
            ]
            lines.append("  ".join(cells))
        return "\n".join(lines)

    if style == "markdown":
        # Header row
        cells = [
            " " + _format_cell(headers[i], widths[i], alignments[i]) + " "
            for i in range(col_count)
        ]
        lines.append(s["vertical"] + s["vertical"].join(cells) + s["vertical"])
        # Separator row
        sep_cells: list[str] = []
        for i in range(col_count):
            if alignments[i] == "right":
                sep_cells.append(" " + s["horizontal"] * (widths[i] - 1) + ":" + " ")
            else:
                sep_cells.append(" " + s["horizontal"] * widths[i] + " ")
        lines.append(s["vertical"] + s["vertical"].join(sep_cells) + s["vertical"])
        # Data rows
        for row in rows:
            cells = [
                " "
                + _format_cell(
                    row[i] if i < len(row) else "", widths[i], alignments[i]
                )
                + " "
                for i in range(col_count)
            ]
            lines.append(s["vertical"] + s["vertical"].join(cells) + s["vertical"])
        return "\n".join(lines)

    # Build horizontal separator lines
    def _h_line(left: str, mid: str, right: str) -> str:
        segments = [s["horizontal"] * (w + 2) for w in widths]
        return left + mid.join(segments) + right

    if style == "compact":
        # No outer borders — compact style
        # Header row
        cells = [
            " " + _format_cell(headers[i], widths[i], alignments[i]) + " "
            for i in range(col_count)
        ]
        lines.append(s["vertical"].join(cells))
        # Separator
        sep_parts = [s["horizontal"] * (w + 2) for w in widths]
        lines.append(s["cross"].join(sep_parts))
        # Data rows
        for row in rows:
            cells = [
                " "
                + _format_cell(
                    row[i] if i < len(row) else "", widths[i], alignments[i]
                )
                + " "
                for i in range(col_count)
            ]
            lines.append(s["vertical"].join(cells))
        return "\n".join(lines)

    # Unicode and ASCII styles (full borders)
    # Top border
    lines.append(_h_line(s["top_left"], s["top_mid"], s["top_right"]))
    # Header row
    cells = [
        " " + _format_cell(headers[i], widths[i], alignments[i]) + " "
        for i in range(col_count)
    ]
    lines.append(s["vertical"] + s["vertical"].join(cells) + s["vertical"])
    # Header separator
    lines.append(_h_line(s["mid_left"], s["mid_mid"], s["mid_right"]))
    # Data rows
    for row in rows:
        cells = [
            " "
            + _format_cell(
                row[i] if i < len(row) else "", widths[i], alignments[i]
            )
            + " "
            for i in range(col_count)
        ]
        lines.append(s["vertical"] + s["vertical"].join(cells) + s["vertical"])
    # Bottom border
    lines.append(_h_line(s["bot_left"], s["bot_mid"], s["bot_right"]))

    return "\n".join(lines)


def from_dicts(
    data: list[dict[str, Any]],
    *,
    style: str = "unicode",
    max_width: int | None = None,
) -> str:
    """Render a table from a list of dictionaries.

    Headers are extracted from dictionary keys (preserving insertion order from
    the first dict, with any extra keys from subsequent dicts appended).

    Args:
        data: List of dictionaries with consistent keys.
        style: Table style.
        max_width: Optional maximum cell width.

    Returns:
        A formatted table string.
    """
    if not data:
        return ""
    seen: dict[str, None] = {}
    for d in data:
        for key in d:
            if key not in seen:
                seen[key] = None
    headers = list(seen)
    rows = [[d.get(h, "") for h in headers] for d in data]
    return table(headers, rows, style=style, max_width=max_width)


def from_csv(
    path: str,
    *,
    style: str = "unicode",
    max_width: int | None = None,
) -> str:
    """Read a CSV file and render it as a table.

    The first row of the CSV is used as headers.

    Args:
        path: Path to the CSV file.
        style: Table style.
        max_width: Optional maximum cell width.

    Returns:
        A formatted table string.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows_iter = iter(reader)
        headers = next(rows_iter)
        rows = list(rows_iter)
    return table(headers, rows, style=style, max_width=max_width)
