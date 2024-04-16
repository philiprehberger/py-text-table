# philiprehberger-text-table

[![Tests](https://github.com/philiprehberger/py-text-table/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-text-table/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-text-table.svg)](https://pypi.org/project/philiprehberger-text-table/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-text-table)](https://github.com/philiprehberger/py-text-table/commits/main)

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
```

### Truncation

```python
print(table(headers, rows, max_width=10))
```

## API

| Function | Description |
|----------|-------------|
| `table(headers, rows, *, style="unicode", max_width=None)` | Render a table from headers and row data |
| `from_dicts(data, *, style="unicode", max_width=None)` | Render a table from a list of dictionaries |
| `from_csv(path, *, style="unicode", max_width=None)` | Read a CSV file and render as a table |

**Styles:** `"unicode"`, `"ascii"`, `"markdown"`, `"minimal"`, `"compact"`

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
