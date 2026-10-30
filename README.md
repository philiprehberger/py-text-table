# philiprehberger-text-table

[![Tests](https://github.com/philiprehberger/py-text-table/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-text-table/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-text-table.svg)](https://pypi.org/project/philiprehberger-text-table/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-text-table)](https://github.com/philiprehberger/py-text-table/commits/main)

![philiprehberger-text-table](https://raw.githubusercontent.com/philiprehberger/py-text-table/main/package-card.webp)

Render data as clean ASCII/Unicode tables in the terminal with zero configuration.

## Installation

```bash
pip install philiprehberger-text-table
```

## Usage

```python
from philiprehberger_text_table import table

headers = ["Name", "Age", "City"]
rows = [
    ["Alice", 30, "New York"],
    ["Bob", 25, "London"],
    ["Charlie", 35, "Tokyo"],
]

print(table(headers, rows))
```

Output:

```
┌─────────┬─────┬──────────┐
│ Name    │ Age │ City     │
├─────────┼─────┼──────────┤
│ Alice   │  30 │ New York │
│ Bob     │  25 │ London   │
│ Charlie │  35 │ Tokyo    │
└─────────┴─────┴──────────┘
```

### From dictionaries

```python
from philiprehberger_text_table import from_dicts

data = [
    {"name": "Alice", "score": 95},
    {"name": "Bob", "score": 87},
]

print(from_dicts(data))
```

### From dataclasses

```python
from dataclasses import dataclass

from philiprehberger_text_table import from_dataclasses


@dataclass
class Person:
    name: str
    age: int


print(from_dataclasses([Person("Alice", 30), Person("Bob", 25)]))
```

Field names become the headers. Passing anything other than dataclass instances raises `TypeError`; an empty list returns `""`.

### Title and footer

```python
headers = ["Item", "Qty", "Price"]
rows = [["Apple", 3, 1.5], ["Banana", 12, 0.25]]

print(table(headers, rows, title="Fruit Stand", footer=["Total", 15, ""]))
```

Output:

```
┌──────────────────────┐
│     Fruit Stand      │
├────────┬─────┬───────┤
│ Item   │ Qty │ Price │
├────────┼─────┼───────┤
│ Apple  │   3 │   1.5 │
│ Banana │  12 │  0.25 │
├────────┼─────┼───────┤
│ Total  │  15 │       │
└────────┴─────┴───────┘
```

The title is centered across the full table width; if it is wider than the table, the last column widens to fit, and `max_width` truncates it like any cell. The footer must have one cell per header (`ValueError` otherwise), counts toward column widths, and uses each column's alignment. In `"minimal"` and `"compact"` styles the footer sits below a dashed separator and the title is a centered line. In `"markdown"` the title is a plain line followed by a blank line, and the footer is the last row with no extra separator (Markdown tables allow only one delimiter row).

### From CSV

```python
from philiprehberger_text_table import from_csv

print(from_csv("data.csv"))
```

### Styles

```python
# ASCII style
print(table(headers, rows, style="ascii"))

# Markdown style
print(table(headers, rows, style="markdown"))

# Minimal style (no borders)
print(table(headers, rows, style="minimal"))

# Compact style (no outer borders)
print(table(headers, rows, style="compact"))

# Rounded Unicode corners
print(table(headers, rows, style="rounded"))

# Double-line borders
print(table(headers, rows, style="double"))
```

### Column alignment

```python
# Override auto-detection for all columns
print(table(headers, rows, align="center"))

# Per-column alignment
print(table(headers, rows, align=["left", "center", "right"]))
```

### From CSV string

```python
from philiprehberger_text_table import from_csv_string

csv_data = "Name,Age\nAlice,30\nBob,25"
print(from_csv_string(csv_data))
```

### From JSON

```python
from philiprehberger_text_table import from_json, from_json_string

# List of dicts (keys become headers)
print(from_json_string('[{"name":"Alice","age":30},{"name":"Bob","age":25}]'))

# List of lists (first inner list is the header row)
print(from_json_string('[["Name","Age"],["Alice",30],["Bob",25]]'))

# Read from a file
print(from_json("data.json"))
```

### Truncation

```python
print(table(headers, rows, max_width=10))
```

### Round-tripping CSV

```python
from philiprehberger_text_table import to_csv, from_csv

csv_text = to_csv(
    [["Alice", 30], ["Bob", 25]],
    headers=["Name", "Age"],
    file="people.csv",  # optional — also writes to disk
)
print(csv_text)
# Name,Age
# Alice,30
# Bob,25

# Re-read and render
print(from_csv("people.csv"))
```

### Round-tripping JSON

```python
from philiprehberger_text_table import to_json, from_json_string

json_text = to_json(
    [["Alice", 30], ["Bob", 25]],
    headers=["name", "age"],  # omit for a plain array of arrays
)
print(json_text)
# [
#   {"name": "Alice", "age": 30},
#   {"name": "Bob", "age": 25}
# ]

# Re-render as a table
print(from_json_string(json_text))
```

### Computing column widths

```python
from philiprehberger_text_table import column_widths

widths = column_widths(["name", "count"], [["alice", 100], ["bob", 5]])
# [5, 5]  — max of header and cell str-lengths per column
```

## API

| Function / Class | Description |
|------------------|-------------|
| `table(headers, rows, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Render a table from headers and row data, with an optional centered `title` and summary `footer` row |
| `from_dicts(data, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Render a table from a list of dictionaries |
| `from_dataclasses(items, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Render a table from a list of dataclass instances (field names become headers) |
| `from_csv(path, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Read a CSV file and render as a table |
| `from_csv_string(text, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Render a table from CSV string content |
| `from_json(path, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Read a JSON file and render as a table (list of dicts or list of lists) |
| `from_json_string(text, *, style="unicode", max_width=None, align=None, title=None, footer=None)` | Render a table from a JSON string |
| `to_csv(rows, *, headers=None, file=None)` | Render rows back to a CSV string (round-trips with `from_csv`); optionally writes to a file |
| `to_json(rows, *, headers=None, file=None, indent=2)` | Render rows to a JSON string (round-trips with `from_json`); optionally writes to a file |
| `column_widths(headers, rows)` | Return the per-column widths the renderer would compute |

### Style values

| Style | Description |
|-------|-------------|
| `"unicode"` | Box-drawing borders (default) |
| `"rounded"` | Box-drawing borders with rounded corners |
| `"double"` | Double-line box-drawing borders |
| `"ascii"` | `+`, `-`, and `\|` borders |
| `"markdown"` | GitHub-flavored Markdown table |
| `"minimal"` | No borders, dashed header separator |
| `"compact"` | Inner separators only, no outer borders |

### Alignment values

| Alignment | Description |
|-----------|-------------|
| `None` | Auto-detect (default): numeric columns right-aligned, others left-aligned |
| `"left"` | Left-align cells |
| `"right"` | Right-align cells |
| `"center"` | Center cells |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-text-table)

🐛 [Report issues](https://github.com/philiprehberger/py-text-table/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-text-table/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)
