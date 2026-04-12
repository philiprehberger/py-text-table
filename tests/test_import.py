"""Basic import test."""


def test_import() -> None:
    """Verify the package can be imported and exports are available."""
    import philiprehberger_text_table

    assert hasattr(philiprehberger_text_table, "table")
    assert hasattr(philiprehberger_text_table, "from_dicts")
    assert hasattr(philiprehberger_text_table, "from_csv")
    assert hasattr(philiprehberger_text_table, "from_csv_string")
