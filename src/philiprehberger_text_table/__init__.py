"""Render data as clean ASCII/Unicode tables in the terminal with zero configuration."""

from __future__ import annotations

import csv
import dataclasses
import io
import json
from pathlib import Path
from typing import Any, Sequence

__all__ = [
    "table",
    "from_dicts",
    "from_dataclasses",
    "from_csv",
    "from_csv_string",
    "from_json",
    "from_json_string",
    "to_csv",
    "to_json",
    "column_widths",
]

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
    "rounded": {
        "top_left": "\u256d",
        "top_mid": "\u252c",
        "top_right": "\u256e",
        "mid_left": "\u251c",
        "mid_mid": "\u253c",
        "mid_right": "\u2524",
        "bot_left": "\u2570",
        "bot_mid": "\u2534",
        "bot_right": "\u256f",
        "horizontal": "\u2500",
        "vertical": "\u2502",
        "cross": "\u253c",
    },
    "double": {
        "top_left": "\u2554",
        "top_mid": "\u2566",
        "top_right": "\u2557",
        "mid_left": "\u2560",
        "mid_mid": "\u256c",
        "mid_right": "\u2563",
        "bot_left": "\u255a",
        "bot_mid": "\u2569",
        "bot_right": "\u255d",
        "horizontal": "\u2550",
        "vertical": "\u2551",
        "cross": "\u256c",
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
    if align == "center":
        return text.center(width)
    return text.ljust(width)


def _truncate(value: Any, max_width: int) -> str:
    """Truncate a value to max_width, adding ellipsis if needed."""
    text = str(value)
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3] + "..."


def _resolve_alignments(
    align: str | list[str] | None,
    rows: list[list[Any]],
    col_count: int,
) -> list[str]:
    """Resolve the per-column alignment list."""
    _valid_alignments = {"left", "right", "center"}
    if align is None:
        # Auto-detect: right for numeric columns, left otherwise
        alignments: list[str] = []
        for col in range(col_count):
            col_values = [row[col] for row in rows if col < len(row)]
            if col_values and all(_is_numeric(v) for v in col_values):
                alignments.append("right")
            else:
                alignments.append("left")
        return alignments
    if isinstance(align, str):
        if align not in _valid_alignments:
            raise ValueError(
                f"Unknown alignment {align!r}. Choose from: {', '.join(sorted(_valid_alignments))}"
            )
        return [align] * col_count
    if len(align) != col_count:
        raise ValueError(
            f"align list length ({len(align)}) must match header count ({col_count})"
        )
    for a in align:
        if a not in _valid_alignments:
            raise ValueError(
                f"Unknown alignment {a!r}. Choose from: {', '.join(sorted(_valid_alignments))}"
            )
    return list(align)


def table(
    headers: list[str],
    rows: list[list[Any]],
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Render a table string from headers and rows.

    Args:
        headers: Column header strings.
        rows: List of rows, each a list of cell values.
        style: Table style — "unicode", "rounded", "double", "ascii", "markdown", "minimal", or "compact".
        max_width: Optional maximum width per cell. Cells exceeding this are truncated
            with "..." appended. The title and footer cells are truncated the same way.
        align: Column alignment override. A single string ("left", "right", "center")
            applies to all columns. A list of strings sets alignment per column.
            When ``None`` (default), numeric columns are right-aligned and others
            are left-aligned.
        title: Optional caption centered across the full table width above the
            header. If it is wider than the table, the last column is widened to
            fit. For ``"markdown"`` it is emitted as a plain line followed by a
            blank line above the table.
        footer: Optional summary row (e.g. totals) with one cell per header. It
            counts toward column widths, uses each column's alignment, and is
            separated from the body by a separator line in the current style
            (for ``"markdown"``, which allows only one delimiter row, it is
            rendered as the final row with no extra separator).

    Returns:
        A formatted table string.

    Raises:
        ValueError: If *style* or *align* is invalid, or *footer* length does
            not match the header count.
    """
    if style not in _STYLES:
        raise ValueError(
            f"Unknown style {style!r}. Choose from: {', '.join(_STYLES)}"
        )

    s = _STYLES[style]
    col_count = len(headers)

    footer_row: list[Any] | None = None
    if footer is not None:
        footer_row = list(footer)
        if len(footer_row) != col_count:
            raise ValueError(
                f"footer length ({len(footer_row)}) must match header count ({col_count})"
            )

    # Apply truncation if max_width is set
    if max_width is not None:
        headers = [_truncate(h, max_width) for h in headers]
        rows = [[_truncate(cell, max_width) for cell in row] for row in rows]
        if footer_row is not None:
            footer_row = [_truncate(cell, max_width) for cell in footer_row]
        if title is not None:
            title = _truncate(title, max_width)

    widths = _calculate_widths(
        headers, rows + ([footer_row] if footer_row is not None else [])
    )

    alignments = _resolve_alignments(align, rows, col_count)

    def _cells(row: list[Any]) -> list[str]:
        return [
            _format_cell(row[i] if i < len(row) else "", widths[i], alignments[i])
            for i in range(col_count)
        ]

    def _padded(row: list[Any]) -> list[str]:
        return [" " + c + " " for c in _cells(row)]

    # Widen the last column so a long title fits (not for markdown, whose
    # title is a free-standing line).
    if title is not None and style != "markdown" and widths:
        if style == "minimal":
            inner = sum(widths) + 2 * (len(widths) - 1)
        else:
            inner = sum(w + 2 for w in widths) + (len(widths) - 1) - 2
        if len(title) > inner:
            widths[-1] += len(title) - inner

    lines: list[str] = []

    if style == "minimal":
        if title is not None:
            total = sum(widths) + 2 * (len(widths) - 1)
            lines.append(title.center(total))
        lines.append("  ".join(_cells(headers)))
        sep = "  ".join("-" * w for w in widths)
        lines.append(sep)
        for row in rows:
            lines.append("  ".join(_cells(row)))
        if footer_row is not None:
            lines.append(sep)
            lines.append("  ".join(_cells(footer_row)))
        return "\n".join(lines)

    if style == "markdown":
        if title is not None:
            lines.append(title)
            lines.append("")
        v = s["vertical"]
        lines.append(v + v.join(_padded(headers)) + v)
        sep_cells: list[str] = []
        for i in range(col_count):
            if alignments[i] == "right":
                sep_cells.append(" " + s["horizontal"] * (widths[i] - 1) + ":" + " ")
            elif alignments[i] == "center":
                sep_cells.append(" :" + s["horizontal"] * (widths[i] - 2) + ":" + " ")
            else:
                sep_cells.append(" " + s["horizontal"] * widths[i] + " ")
        lines.append(v + v.join(sep_cells) + v)
        for row in rows:
            lines.append(v + v.join(_padded(row)) + v)
        if footer_row is not None:
            lines.append(v + v.join(_padded(footer_row)) + v)
        return "\n".join(lines)

    segments = [s["horizontal"] * (w + 2) for w in widths]

    def _h_line(left: str, mid: str, right: str) -> str:
        return left + mid.join(segments) + right

    if style == "compact":
        # No outer borders — compact style
        v = s["vertical"]
        if title is not None:
            total = sum(w + 2 for w in widths) + (len(widths) - 1)
            lines.append(" " + title.center(max(total - 2, 0)) + " ")
            lines.append(s["horizontal"] * total)
        lines.append(v.join(_padded(headers)))
        sep = s["cross"].join(segments)
        lines.append(sep)
        for row in rows:
            lines.append(v.join(_padded(row)))
        if footer_row is not None:
            lines.append(sep)
            lines.append(v.join(_padded(footer_row)))
        return "\n".join(lines)

    # Full-border styles (unicode, rounded, double, ascii)
    v = s["vertical"]
    if title is not None:
        span = sum(w + 2 for w in widths) + (len(widths) - 1)
        lines.append(s["top_left"] + s["horizontal"] * span + s["top_right"])
        lines.append(v + " " + title.center(max(span - 2, 0)) + " " + v)
        lines.append(_h_line(s["mid_left"], s["top_mid"], s["mid_right"]))
    else:
        lines.append(_h_line(s["top_left"], s["top_mid"], s["top_right"]))
    lines.append(v + v.join(_padded(headers)) + v)
    lines.append(_h_line(s["mid_left"], s["mid_mid"], s["mid_right"]))
    for row in rows:
        lines.append(v + v.join(_padded(row)) + v)
    if footer_row is not None:
        lines.append(_h_line(s["mid_left"], s["mid_mid"], s["mid_right"]))
        lines.append(v + v.join(_padded(footer_row)) + v)
    lines.append(_h_line(s["bot_left"], s["bot_mid"], s["bot_right"]))

    return "\n".join(lines)


def from_dicts(
    data: list[dict[str, Any]],
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Render a table from a list of dictionaries.

    Headers are extracted from dictionary keys (preserving insertion order from
    the first dict, with any extra keys from subsequent dicts appended).

    Args:
        data: List of dictionaries with consistent keys.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

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
    return table(
        headers, rows, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def from_dataclasses(
    items: Sequence[Any],
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Render a table from a sequence of dataclass instances.

    Field names (from :func:`dataclasses.fields`) become the headers, in
    declaration order. When instances of different dataclasses are mixed,
    fields are merged in first-seen order and missing values render as ``""``.
    Values are read with ``getattr`` (nested dataclasses are not expanded).

    Args:
        items: Dataclass instances.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

    Returns:
        A formatted table string, or ``""`` when *items* is empty.

    Raises:
        TypeError: If any item is not a dataclass instance.
    """
    data: list[dict[str, Any]] = []
    for item in items:
        if not dataclasses.is_dataclass(item) or isinstance(item, type):
            raise TypeError(
                f"from_dataclasses() expects dataclass instances, got {type(item).__name__}"
            )
        data.append({f.name: getattr(item, f.name) for f in dataclasses.fields(item)})
    return from_dicts(
        data, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def from_csv(
    path: str,
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Read a CSV file and render it as a table.

    The first row of the CSV is used as headers.

    Args:
        path: Path to the CSV file.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

    Returns:
        A formatted table string.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows_iter = iter(reader)
        headers = next(rows_iter)
        rows = list(rows_iter)
    return table(
        headers, rows, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def from_csv_string(
    text: str,
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Render a table from CSV-formatted string content.

    The first row of the CSV is used as headers.

    Args:
        text: CSV-formatted string.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

    Returns:
        A formatted table string.
    """
    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)
    headers = next(rows_iter)
    rows = list(rows_iter)
    return table(
        headers, rows, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def _render_json_payload(
    payload: Any,
    *,
    style: str,
    max_width: int | None,
    align: str | list[str] | None,
    title: str | None,
    footer: Sequence[Any] | None,
) -> str:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return from_dicts(
            payload, style=style, max_width=max_width, align=align, title=title, footer=footer
        )
    if isinstance(payload, list) and all(isinstance(item, list) for item in payload):
        if not payload:
            return ""
        headers = [str(h) for h in payload[0]]
        rows = [list(row) for row in payload[1:]]
        return table(
            headers, rows, style=style, max_width=max_width, align=align, title=title, footer=footer
        )
    raise ValueError(
        "Unsupported JSON shape: expected a list of dicts or a list of lists"
    )


def from_json(
    path: str | Path,
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Read a JSON file and render it as a table.

    Accepts either a list of dicts (keys become headers in first-seen order)
    or a list of lists where the first inner list is the header row.

    Args:
        path: Path to the JSON file.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

    Returns:
        A formatted table string.

    Raises:
        ValueError: If the JSON payload is neither a list of dicts nor a list of lists.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return _render_json_payload(
        payload, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def from_json_string(
    text: str,
    *,
    style: str = "unicode",
    max_width: int | None = None,
    align: str | list[str] | None = None,
    title: str | None = None,
    footer: Sequence[Any] | None = None,
) -> str:
    """Render a table from JSON-formatted string content.

    Accepts either a list of dicts or a list of lists with a leading header row.

    Args:
        text: JSON-formatted string.
        style: Table style.
        max_width: Optional maximum cell width.
        align: Column alignment override (see :func:`table`).
        title: Optional caption above the table (see :func:`table`).
        footer: Optional summary row below the body (see :func:`table`).

    Returns:
        A formatted table string.

    Raises:
        ValueError: If the JSON payload is neither a list of dicts nor a list of lists.
    """
    payload = json.loads(text)
    return _render_json_payload(
        payload, style=style, max_width=max_width, align=align, title=title, footer=footer
    )


def to_csv(
    rows: list[list[Any]],
    *,
    headers: list[str] | None = None,
    file: str | Path | None = None,
) -> str:
    """Render *rows* as CSV. Round-trips with from_csv().

    Args:
        rows: 2D row data.
        headers: Optional header row.
        file: If provided, write the CSV to this path (and still return the string).

    Returns:
        The full CSV string (including the header row when *headers* is given).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    if headers is not None:
        writer.writerow([str(h) for h in headers])
    writer.writerows([[str(cell) for cell in row] for row in rows])
    result = buf.getvalue()
    if file is not None:
        Path(file).write_text(result, encoding="utf-8")
    return result


def to_json(
    rows: list[list[Any]],
    *,
    headers: list[str] | None = None,
    file: str | Path | None = None,
    indent: int | None = 2,
) -> str:
    """Render *rows* as a JSON array. Round-trips with from_json().

    When *headers* is given, each row becomes an object keyed by the headers
    (matching the list-of-dicts shape ``from_json`` accepts). Extra cells beyond
    the header count are dropped and missing cells default to ``""``. Without
    *headers*, the output is a plain array of arrays.

    Args:
        rows: 2D row data.
        headers: Optional header row used as object keys.
        file: If provided, write the JSON to this path (and still return it).
        indent: Indentation passed to ``json.dumps``. Use ``None`` for compact
            output.

    Returns:
        The JSON string.
    """
    payload: Any
    if headers is not None:
        keys = [str(h) for h in headers]
        payload = [
            {keys[i]: (row[i] if i < len(row) else "") for i in range(len(keys))}
            for row in rows
        ]
    else:
        payload = [list(row) for row in rows]
    result = json.dumps(payload, indent=indent, ensure_ascii=False, default=str)
    if file is not None:
        Path(file).write_text(result, encoding="utf-8")
    return result


def column_widths(headers: list[str], rows: list[list[Any]]) -> list[int]:
    """Compute the per-column widths the renderer would use.

    Returns:
        List of widths, one per column, equal to the max str-length across
        the header and every cell in that column.
    """
    if not headers and not rows:
        return []
    col_count = max(len(headers), *(len(row) for row in rows)) if rows else len(headers)
    widths: list[int] = []
    for i in range(col_count):
        header_len = len(str(headers[i])) if i < len(headers) else 0
        cell_lens = [len(str(row[i])) if i < len(row) else 0 for row in rows]
        widths.append(max(header_len, *cell_lens) if cell_lens else header_len)
    return widths
