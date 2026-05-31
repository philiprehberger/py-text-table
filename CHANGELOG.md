# Changelog

## 0.3.0 (2026-05-30)

- Add `to_csv()` for rendering data back to CSV (round-trips with `from_csv`)
- Add `column_widths()` exposing the renderer's computed per-column widths

## 0.2.0 (2026-04-11)

- Add `align` parameter to `table()`, `from_dicts()`, and `from_csv()` for explicit column alignment control
- Add center alignment support (`"left"`, `"right"`, `"center"`)
- Add `from_csv_string()` function for rendering tables from CSV string content
- Add comprehensive test suite (36 tests covering all styles, alignment, truncation, and edge cases)
- Fix CHANGELOG formatting for versions 0.1.7 and 0.1.6

## 0.1.8 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility
- Add GitHub issue templates, dependabot config, and PR template

## 0.1.7

- Standardize README structure and fix compliance issues

## 0.1.6

- Add pytest and mypy tool configuration to pyproject.toml

## 0.1.5

- Add basic import test

## 0.1.4

- Add Development section to README

## 0.1.1

- Re-release for PyPI publishing

## 0.1.0 (2026-03-15)

- Initial release
- Unicode, ASCII, markdown, minimal, and compact table styles
- `from_dicts()` for rendering tables from list of dictionaries
- `from_csv()` for rendering tables from CSV files
- Auto right-alignment for numeric columns
- Optional cell truncation with `max_width`
