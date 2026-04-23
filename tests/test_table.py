"""Tests for the table rendering functions."""

from __future__ import annotations

import os
import tempfile

import pytest

from philiprehberger_text_table import from_csv, from_csv_string, from_dicts, table


HEADERS = ["Name", "Age", "City"]
ROWS = [
    ["Alice", 30, "New York"],
    ["Bob", 25, "London"],
    ["Charlie", 35, "Tokyo"],
]


class TestTableUnicode:
    def test_basic_output(self) -> None:
        result = table(HEADERS, ROWS)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result

    def test_unicode_borders(self) -> None:
        result = table(HEADERS, ROWS)
        assert "\u250c" in result  # top-left corner
        assert "\u2518" in result  # bottom-right corner
        assert "\u2502" in result  # vertical

    def test_numeric_right_alignment(self) -> None:
        result = table(HEADERS, ROWS)
        lines = result.split("\n")
        # Age column should be right-aligned (30 should have leading space)
        header_line = lines[1]
        assert " 30 " in lines[3] or "  30 " in lines[3]


class TestTableStyles:
    def test_ascii_style(self) -> None:
        result = table(HEADERS, ROWS, style="ascii")
        assert "+" in result
        assert "-" in result
        assert "|" in result
        assert "\u250c" not in result

    def test_markdown_style(self) -> None:
        result = table(HEADERS, ROWS, style="markdown")
        lines = result.split("\n")
        # Markdown has header separator with dashes
        assert "---" in lines[1]
        # All lines start and end with |
        for line in lines:
            assert line.startswith("|")
            assert line.endswith("|")

    def test_markdown_right_align_indicator(self) -> None:
        result = table(HEADERS, ROWS, style="markdown")
        lines = result.split("\n")
        sep = lines[1]
        # Age column is numeric, separator should end with :
        assert ":" in sep

    def test_minimal_style(self) -> None:
        result = table(HEADERS, ROWS, style="minimal")
        assert "|" not in result
        assert "+" not in result
        assert "\u250c" not in result

    def test_compact_style(self) -> None:
        result = table(HEADERS, ROWS, style="compact")
        lines = result.split("\n")
        # Compact has no outer borders but has inner separators
        assert "|" in lines[0]
        assert "+" in lines[1]

    def test_invalid_style_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown style"):
            table(HEADERS, ROWS, style="fancy")


class TestTruncation:
    def test_max_width_truncates(self) -> None:
        result = table(HEADERS, [["LongNameHere", 1, "X"]], max_width=6)
        assert "Lon..." in result

    def test_max_width_no_truncation_needed(self) -> None:
        result = table(["A"], [["Hi"]], max_width=10)
        assert "Hi" in result
        assert "..." not in result

    def test_max_width_very_short(self) -> None:
        result = table(["Name"], [["Hello"]], max_width=2)
        assert "He" in result


class TestAlign:
    def test_align_single_left(self) -> None:
        result = table(HEADERS, ROWS, align="left")
        lines = result.split("\n")
        # All data should be left-aligned, including numbers
        assert "30 " in lines[3]

    def test_align_single_right(self) -> None:
        result = table(["A"], [["Hi"], ["World"]], align="right")
        lines = result.split("\n")
        # Data rows start at index 3 (border, header, separator, data...)
        assert "   Hi" in lines[3]

    def test_align_single_center(self) -> None:
        result = table(["Name"], [["A"], ["Bob"]], align="center")
        assert result  # basic rendering works

    def test_align_per_column(self) -> None:
        result = table(HEADERS, ROWS, align=["left", "center", "right"])
        assert result

    def test_align_invalid_string(self) -> None:
        with pytest.raises(ValueError, match="Unknown alignment"):
            table(HEADERS, ROWS, align="top")

    def test_align_invalid_in_list(self) -> None:
        with pytest.raises(ValueError, match="Unknown alignment"):
            table(HEADERS, ROWS, align=["left", "top", "right"])

    def test_align_wrong_length(self) -> None:
        with pytest.raises(ValueError, match="must match header count"):
            table(HEADERS, ROWS, align=["left", "right"])

    def test_markdown_center_indicator(self) -> None:
        result = table(HEADERS, ROWS, style="markdown", align=["left", "center", "right"])
        lines = result.split("\n")
        sep = lines[1]
        # Center column should have : on both sides
        parts = sep.split("|")
        center_part = parts[2].strip()
        assert center_part.startswith(":")
        assert center_part.endswith(":")


class TestFromDicts:
    def test_basic(self) -> None:
        data = [
            {"name": "Alice", "score": 95},
            {"name": "Bob", "score": 87},
        ]
        result = from_dicts(data)
        assert "Alice" in result
        assert "Bob" in result
        assert "95" in result

    def test_empty_list(self) -> None:
        assert from_dicts([]) == ""

    def test_missing_keys(self) -> None:
        data = [
            {"a": 1, "b": 2},
            {"a": 3, "c": 4},
        ]
        result = from_dicts(data)
        assert "1" in result
        assert "3" in result

    def test_with_align(self) -> None:
        data = [{"x": "a", "y": "b"}]
        result = from_dicts(data, align="center")
        assert result


class TestFromCsv:
    def test_basic(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("Name,Age\nAlice,30\nBob,25\n")
            path = f.name
        try:
            result = from_csv(path)
            assert "Alice" in result
            assert "30" in result
        finally:
            os.unlink(path)

    def test_with_style(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("A,B\n1,2\n")
            path = f.name
        try:
            result = from_csv(path, style="ascii")
            assert "+" in result
        finally:
            os.unlink(path)


class TestFromCsvString:
    def test_basic(self) -> None:
        csv_data = "Name,Age\nAlice,30\nBob,25"
        result = from_csv_string(csv_data)
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result

    def test_with_style(self) -> None:
        csv_data = "A,B\n1,2"
        result = from_csv_string(csv_data, style="markdown")
        assert "|" in result

    def test_with_align(self) -> None:
        csv_data = "X,Y\na,b"
        result = from_csv_string(csv_data, align="right")
        assert result

    def test_with_max_width(self) -> None:
        csv_data = "Name\nVeryLongNameHere"
        result = from_csv_string(csv_data, max_width=8)
        assert "..." in result


class TestEdgeCases:
    def test_single_column(self) -> None:
        result = table(["X"], [["a"], ["b"]])
        assert "a" in result
        assert "b" in result

    def test_single_row(self) -> None:
        result = table(["A", "B"], [["x", "y"]])
        assert "x" in result

    def test_empty_rows(self) -> None:
        result = table(["A"], [])
        assert "A" in result

    def test_mismatched_row_length(self) -> None:
        result = table(["A", "B", "C"], [["x"]])
        assert "x" in result

    def test_all_styles_render(self) -> None:
        for style in ("unicode", "ascii", "markdown", "minimal", "compact"):
            result = table(["H"], [["v"]], style=style)
            assert "v" in result
