"""Tests for the table rendering functions."""

from __future__ import annotations

import os
import tempfile

import json
from dataclasses import dataclass

import pytest

from philiprehberger_text_table import (
    column_widths,
    from_csv,
    from_csv_string,
    from_dataclasses,
    from_dicts,
    from_json,
    from_json_string,
    table,
    to_csv,
    to_json,
)


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


class TestToCsv:
    def test_basic_with_headers(self) -> None:
        result = to_csv([["a", 1], ["b", 2]], headers=["name", "count"])
        assert result == "name,count\r\na,1\r\nb,2\r\n"

    def test_empty(self) -> None:
        assert to_csv([]) == ""

    def test_file_round_trip(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        out = tmp_path / "out.csv"
        csv_string = to_csv(
            [["Alice", 30], ["Bob", 25]],
            headers=["Name", "Age"],
            file=out,
        )
        # File bytes match exactly (read_text would apply universal-newline
        # translation, masking the \r\n line terminators csv.writer emits).
        assert out.read_bytes() == csv_string.encode("utf-8")
        rendered = from_csv(str(out))
        assert "Alice" in rendered
        assert "Bob" in rendered
        assert "30" in rendered

    def test_no_headers(self) -> None:
        result = to_csv([["a", "b"], ["c", "d"]])
        assert result == "a,b\r\nc,d\r\n"

    def test_coerces_non_strings(self) -> None:
        result = to_csv([[1, 2.5]], headers=["x", "y"])
        assert result == "x,y\r\n1,2.5\r\n"


class TestRoundedStyle:
    def test_rounded_corners(self) -> None:
        result = table(HEADERS, ROWS, style="rounded")
        # rounded corners
        assert "╭" in result  # ╭
        assert "╮" in result  # ╮
        assert "╯" in result  # ╯
        assert "╰" in result  # ╰
        # square corners must not appear
        assert "┌" not in result  # ┌
        assert "┐" not in result  # ┐

    def test_rounded_renders_data(self) -> None:
        result = table(HEADERS, ROWS, style="rounded")
        assert "Alice" in result
        assert "30" in result

    def test_rounded_listed_in_styles(self) -> None:
        result = table(["H"], [["v"]], style="rounded")
        assert "v" in result


class TestFromJsonString:
    def test_list_of_dicts(self) -> None:
        text = '[{"name":"Alice","age":30},{"name":"Bob","age":25}]'
        result = from_json_string(text)
        assert "Alice" in result
        assert "30" in result
        assert "Bob" in result

    def test_list_of_lists_with_header(self) -> None:
        text = '[["Name","Age"],["Alice",30],["Bob",25]]'
        result = from_json_string(text)
        assert "Name" in result
        assert "Alice" in result
        assert "25" in result

    def test_empty_list_of_lists(self) -> None:
        assert from_json_string("[]") == ""

    def test_with_style(self) -> None:
        result = from_json_string('[{"a":1}]', style="markdown")
        assert "|" in result

    def test_unsupported_shape(self) -> None:
        with pytest.raises(ValueError, match="Unsupported JSON shape"):
            from_json_string('{"a": 1}')

    def test_mixed_list_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported JSON shape"):
            from_json_string('[{"a":1}, ["b", 2]]')


class TestFromJson:
    def test_list_of_dicts(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "data.json"
        path.write_text('[{"name":"Alice","age":30}]', encoding="utf-8")
        result = from_json(str(path))
        assert "Alice" in result
        assert "30" in result

    def test_list_of_lists(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "data.json"
        path.write_text('[["A","B"],["x","y"]]', encoding="utf-8")
        result = from_json(path)
        assert "A" in result
        assert "x" in result

    def test_with_max_width(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "data.json"
        path.write_text('[{"col":"VeryLongValueHere"}]', encoding="utf-8")
        result = from_json(str(path), max_width=8)
        assert "..." in result


class TestDoubleStyle:
    def test_double_corners(self) -> None:
        result = table(HEADERS, ROWS, style="double")
        for ch in ("╔", "╗", "╚", "╝", "║", "═", "╬"):
            assert ch in result
        # single-line corners must not appear
        assert "┌" not in result
        assert "│" not in result

    def test_double_renders_data(self) -> None:
        result = table(HEADERS, ROWS, style="double")
        assert "Alice" in result
        assert "30" in result


class TestToJson:
    def test_with_headers_is_list_of_dicts(self) -> None:
        result = to_json([["Alice", 30], ["Bob", 25]], headers=["name", "age"])
        assert json.loads(result) == [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]

    def test_without_headers_is_list_of_lists(self) -> None:
        result = to_json([["a", 1], ["b", 2]])
        assert json.loads(result) == [["a", 1], ["b", 2]]

    def test_round_trips_with_from_json_string(self) -> None:
        rows = [["Alice", 30], ["Bob", 25]]
        text = to_json(rows, headers=["name", "age"])
        rendered = from_json_string(text)
        assert "Alice" in rendered
        assert "30" in rendered

    def test_missing_cells_default_to_empty(self) -> None:
        result = to_json([["Alice"]], headers=["name", "age"])
        assert json.loads(result) == [{"name": "Alice", "age": ""}]

    def test_writes_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "out.json"
        to_json([["a", 1]], headers=["x", "y"], file=str(path))
        assert json.loads(path.read_text(encoding="utf-8")) == [{"x": "a", "y": 1}]

    def test_compact_indent_none(self) -> None:
        result = to_json([["a", 1]], headers=["x", "y"], indent=None)
        assert "\n" not in result


class TestColumnWidths:
    def test_basic(self) -> None:
        widths = column_widths(["name", "count"], [["alice", 100], ["bob", 5]])
        assert widths == [5, 5]

    def test_empty(self) -> None:
        assert column_widths([], []) == []

    def test_headers_only(self) -> None:
        assert column_widths(["abc", "de"], []) == [3, 2]

    def test_missing_cells_treated_as_empty(self) -> None:
        widths = column_widths(["a", "bb", "ccc"], [["x"]])
        assert widths == [1, 2, 3]


FRUIT_HEADERS = ["Item", "Qty", "Price"]
FRUIT_ROWS: list[list[object]] = [["Apple", 3, 1.5], ["Banana", 12, 0.25]]
FRUIT_FOOTER = ["Total", 15, ""]


class TestTitleAndFooter:
    def test_unicode_title_and_footer(self) -> None:
        result = table(FRUIT_HEADERS, FRUIT_ROWS, title="Fruit Stand", footer=FRUIT_FOOTER)
        assert result == (
            "\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
            "\u2502     Fruit Stand      \u2502\n"
            "\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524\n"
            "\u2502 Item   \u2502 Qty \u2502 Price \u2502\n"
            "\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524\n"
            "\u2502 Apple  \u2502   3 \u2502   1.5 \u2502\n"
            "\u2502 Banana \u2502  12 \u2502  0.25 \u2502\n"
            "\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524\n"
            "\u2502 Total  \u2502  15 \u2502       \u2502\n"
            "\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518"
        )

    def test_ascii_title_and_footer(self) -> None:
        result = table(
            FRUIT_HEADERS, FRUIT_ROWS, style="ascii", title="Fruit Stand", footer=FRUIT_FOOTER
        )
        assert result == (
            "+----------------------+\n"
            "|     Fruit Stand      |\n"
            "+--------+-----+-------+\n"
            "| Item   | Qty | Price |\n"
            "+--------+-----+-------+\n"
            "| Apple  |   3 |   1.5 |\n"
            "| Banana |  12 |  0.25 |\n"
            "+--------+-----+-------+\n"
            "| Total  |  15 |       |\n"
            "+--------+-----+-------+"
        )

    def test_markdown_title_and_footer(self) -> None:
        result = table(
            FRUIT_HEADERS, FRUIT_ROWS, style="markdown", title="Fruit Stand", footer=FRUIT_FOOTER
        )
        assert result == (
            "Fruit Stand\n"
            "\n"
            "| Item   | Qty | Price |\n"
            "| ------ | --: | ----: |\n"
            "| Apple  |   3 |   1.5 |\n"
            "| Banana |  12 |  0.25 |\n"
            "| Total  |  15 |       |"
        )

    def test_minimal_title_and_footer(self) -> None:
        result = table(
            FRUIT_HEADERS, FRUIT_ROWS, style="minimal", title="Fruit Stand", footer=FRUIT_FOOTER
        )
        assert result == (
            "   Fruit Stand    \n"
            "Item    Qty  Price\n"
            "------  ---  -----\n"
            "Apple     3    1.5\n"
            "Banana   12   0.25\n"
            "------  ---  -----\n"
            "Total    15       "
        )

    def test_compact_title_and_footer(self) -> None:
        result = table(
            FRUIT_HEADERS, FRUIT_ROWS, style="compact", title="Fruit Stand", footer=FRUIT_FOOTER
        )
        assert result == (
            "     Fruit Stand      \n"
            "----------------------\n"
            " Item   | Qty | Price \n"
            "--------+-----+-------\n"
            " Apple  |   3 |   1.5 \n"
            " Banana |  12 |  0.25 \n"
            "--------+-----+-------\n"
            " Total  |  15 |       "
        )

    def test_double_title_uses_tee_joints(self) -> None:
        lines = table(["A", "B"], [["x", "y"]], style="double", title="T").split("\n")
        assert lines[0] == "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557"
        assert lines[1] == "\u2551   T   \u2551"
        assert lines[2] == "\u2560\u2550\u2550\u2550\u2566\u2550\u2550\u2550\u2563"

    def test_title_only_ascii(self) -> None:
        result = table(["A", "B"], [["x", "y"]], style="ascii", title="Hi")
        assert result == (
            "+-------+\n"
            "|   Hi  |\n"
            "+---+---+\n"
            "| A | B |\n"
            "+---+---+\n"
            "| x | y |\n"
            "+---+---+"
        )

    def test_long_title_widens_last_column(self) -> None:
        result = table(["A", "B"], [["x", "y"]], style="ascii", title="A long title")
        assert result == (
            "+--------------+\n"
            "| A long title |\n"
            "+---+----------+\n"
            "| A | B        |\n"
            "+---+----------+\n"
            "| x | y        |\n"
            "+---+----------+"
        )

    def test_title_truncated_by_max_width(self) -> None:
        result = table(["A", "B"], [["x", "y"]], style="ascii", title="A long title", max_width=8)
        assert result.split("\n")[1] == "| A lon... |"

    def test_footer_only_ascii(self) -> None:
        result = table(["Name", "N"], [["a", 1]], style="ascii", footer=["Sum", 1])
        assert result == (
            "+------+---+\n"
            "| Name | N |\n"
            "+------+---+\n"
            "| a    | 1 |\n"
            "+------+---+\n"
            "| Sum  | 1 |\n"
            "+------+---+"
        )

    def test_footer_widens_column(self) -> None:
        result = table(["A"], [["x"]], style="minimal", footer=["Grand total"])
        assert result == "A          \n-----------\nx          \n-----------\nGrand total"

    def test_footer_truncated_by_max_width(self) -> None:
        result = table(["A"], [["x"]], style="minimal", footer=["Grand total"], max_width=6)
        assert result.split("\n")[-1] == "Gra..."

    def test_footer_accepts_tuple(self) -> None:
        result = table(["A", "B"], [["x", 1]], footer=("t", 1))
        assert "\u2502 t \u2502 1 \u2502" in result

    def test_footer_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="footer length"):
            table(["A", "B"], [["x", "y"]], footer=["only one"])

    def test_footer_does_not_change_auto_alignment(self) -> None:
        result = table(["Item", "Qty"], [["a", 3]], style="markdown", footer=["Total", 3])
        assert result.split("\n")[1] == "| ----- | --: |"

    def test_from_dicts_title_and_footer(self) -> None:
        data = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 87}]
        result = from_dicts(data, style="ascii", title="Scores", footer=["Avg", 91])
        assert result == (
            "+---------------+\n"
            "|     Scores    |\n"
            "+-------+-------+\n"
            "| name  | score |\n"
            "+-------+-------+\n"
            "| Alice |    95 |\n"
            "| Bob   |    87 |\n"
            "+-------+-------+\n"
            "| Avg   |    91 |\n"
            "+-------+-------+"
        )

    def test_from_csv_string_title(self) -> None:
        result = from_csv_string("A,B\nx,y", style="markdown", title="CSV")
        assert result.startswith("CSV\n\n| A | B |")

    def test_from_csv_footer(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "d.csv"
        path.write_text("A,B\nx,y\n", encoding="utf-8")
        result = from_csv(str(path), style="minimal", footer=["f", "g"])
        assert result.split("\n")[-1] == "f  g"

    def test_from_json_string_title_and_footer(self) -> None:
        result = from_json_string(
            '[["A","B"],["x","y"]]', style="minimal", title="J", footer=["1", "2"]
        )
        assert result == " J  \nA  B\n-  -\nx  y\n-  -\n1  2"

    def test_from_json_footer(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        path = tmp_path / "d.json"
        path.write_text('[{"a": 1}]', encoding="utf-8")
        result = from_json(path, style="minimal", footer=[9])
        assert result == "a\n-\n1\n-\n9"

    def test_all_styles_render_title_and_footer(self) -> None:
        for style in ("unicode", "rounded", "double", "ascii", "markdown", "minimal", "compact"):
            result = table(["H"], [["v"]], style=style, title="T", footer=["f"])
            assert "T" in result
            assert "f" in result


@dataclass
class Person:
    name: str
    age: int


@dataclass
class Employee:
    name: str
    team: str


class TestFromDataclasses:
    def test_basic_ascii(self) -> None:
        result = from_dataclasses([Person("Alice", 30), Person("Bob", 25)], style="ascii")
        assert result == (
            "+-------+-----+\n"
            "| name  | age |\n"
            "+-------+-----+\n"
            "| Alice |  30 |\n"
            "| Bob   |  25 |\n"
            "+-------+-----+"
        )

    def test_title_and_footer(self) -> None:
        result = from_dataclasses(
            [Person("Alice", 30), Person("Bob", 25)],
            style="markdown",
            title="People",
            footer=["Total", 55],
        )
        assert result == (
            "People\n"
            "\n"
            "| name  | age |\n"
            "| ----- | --: |\n"
            "| Alice |  30 |\n"
            "| Bob   |  25 |\n"
            "| Total |  55 |"
        )

    def test_empty_list(self) -> None:
        assert from_dataclasses([]) == ""
        assert from_dataclasses([]) == from_dicts([])

    def test_non_dataclass_raises(self) -> None:
        with pytest.raises(TypeError, match="dataclass instances"):
            from_dataclasses([{"name": "Alice"}])

    def test_dataclass_class_raises(self) -> None:
        with pytest.raises(TypeError, match="dataclass instances"):
            from_dataclasses([Person])

    def test_mixed_dataclasses_merge_fields(self) -> None:
        result = from_dataclasses([Person("Alice", 30), Employee("Bob", "Ops")], style="minimal")
        assert result == (
            "name   age  team\n"
            "-----  ---  ----\n"
            "Alice  30       \n"
            "Bob         Ops "
        )

    def test_with_align_and_max_width(self) -> None:
        result = from_dataclasses(
            [Person("Alexandria", 30)], style="minimal", align="left", max_width=6
        )
        assert result == "name    age\n------  ---\nAle...  30 "


def test_from_dataclasses_exported() -> None:
    import philiprehberger_text_table as mod

    assert "from_dataclasses" in mod.__all__
