"""Test that backports.datetime_fromisoformat is only imported on Python < 3.11.

Regression test for issue #2978: on Python 3.11+, importing the backports
compiled extension on ARM Macs can cause a Mach-O architecture crash.
"""
import ast
import sys
from pathlib import Path


def test_backports_not_imported_on_311_plus():
    """On Python 3.11+, importing marshmallow should not load backports."""
    if sys.version_info >= (3, 11):
        import marshmallow

        assert marshmallow is not None
        # Verify no backports modules were loaded
        backports = [
            m
            for m in sys.modules
            if m.startswith("backports.")
        ]
        assert backports == [], f"Unexpected backports loaded: {backports}"


def test_fields_module_uses_version_guard():
    """Verify that fields.py guards the backports import with a version check."""
    source_path = (
        Path(__file__).resolve().parent.parent / "src" / "marshmallow" / "fields.py"
    )
    source = source_path.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if isinstance(node.test, ast.Compare):
                left = node.test.left
                # sys.version_info → Attribute(value=Name(id='sys'), attr='version_info')
                if (
                    isinstance(left, ast.Attribute)
                    and left.attr == "version_info"
                    and isinstance(left.value, ast.Name)
                    and left.value.id == "sys"
                ):
                    return

    raise AssertionError(
        "backports.datetime_fromisoformat import is not guarded by "
        "sys.version_info check in fields.py"
    )


def test_fromisoformat_still_works():
    """Verify that datetime.fromisoformat works (built-in on 3.11+)."""
    import datetime as dt

    result = dt.datetime.fromisoformat("2026-01-15T10:30:00")
    assert result.year == 2026
    assert result.hour == 10
