"""Basic unit tests for samccann.sqlite collection."""

import sqlite_backup
import sqlite_db
import sqlite_query
import sqlite_table


def test_module_imports() -> None:
    """Test that all modules can be imported successfully."""
    assert hasattr(sqlite_backup, "main")
    assert hasattr(sqlite_db, "main")
    assert hasattr(sqlite_query, "main")
    assert hasattr(sqlite_table, "main")


def test_documentation_format() -> None:
    """Test that module documentation is properly formatted."""
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
