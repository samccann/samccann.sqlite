"""Basic unit tests for samccann.sqlite collection."""

import os
import sys


# Add the modules directory to sys.path for importing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../../plugins/modules"),
)


def test_basic() -> None:
    """Basic test that always passes.

    Raises:
        AssertionError: If the assertion fails.
    """
    assert bool(1) is True


def test_module_imports() -> None:
    """Test that all modules can be imported successfully.

    Raises:
        ImportError: If any module cannot be imported.
    """
    try:
        import sqlite_backup
        import sqlite_db
        import sqlite_query
        import sqlite_table

        # Verify modules have the expected main functions
        assert hasattr(sqlite_backup, "main")
        assert hasattr(sqlite_db, "main")
        assert hasattr(sqlite_query, "main")
        assert hasattr(sqlite_table, "main")

        # Verify modules have documentation
        assert hasattr(sqlite_backup, "DOCUMENTATION")
        assert hasattr(sqlite_db, "DOCUMENTATION")
        assert hasattr(sqlite_query, "DOCUMENTATION")
        assert hasattr(sqlite_table, "DOCUMENTATION")

    except ImportError as e:
        raise AssertionError(f"Failed to import module: {e}")


def test_documentation_format() -> None:
    """Test that module documentation is properly formatted.

    Raises:
        AssertionError: If documentation format is invalid.
    """
    import sqlite_backup
    import sqlite_db
    import sqlite_query
    import sqlite_table

    modules = [sqlite_backup, sqlite_db, sqlite_query, sqlite_table]

    for module in modules:
        doc = module.DOCUMENTATION
        assert isinstance(doc, str), f"{module.__name__} DOCUMENTATION must be a string"
        assert "module:" in doc, f"{module.__name__} documentation missing module name"
        assert (
            "short_description:" in doc
        ), f"{module.__name__} documentation missing short_description"
        assert "version_added:" in doc, f"{module.__name__} documentation missing version_added"
        assert "author:" in doc, f"{module.__name__} documentation missing author"
