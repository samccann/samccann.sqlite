"""Unit tests for sqlite_table module."""

import os
import sys

from unittest.mock import MagicMock

import pytest


# Add the modules directory to sys.path for importing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../../plugins/modules"),
)

try:
    from sqlite_table import create_table, drop_table, get_table_info, table_exists
except ImportError:
    # Skip tests if module can't be imported
    pytest.skip("Cannot import sqlite_table module", allow_module_level=True)


class TestSqliteTableFunctions:
    """Test class for sqlite_table utility functions."""

    def test_table_exists_true(self):
        """Test table_exists returns True when table exists."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("users",)
        assert table_exists(mock_cursor, "users") is True
        mock_cursor.execute.assert_called_once()

    def test_table_exists_false(self):
        """Test table_exists returns False when table doesn't exist."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        assert table_exists(mock_cursor, "nonexistent") is False

    def test_get_table_info(self):
        """Test get_table_info returns correct information."""
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("name",),
            ("type",),
            ("notnull",),
            ("dflt_value",),
            ("pk",),
        ]
        mock_cursor.fetchall.return_value = [
            ("id", "INTEGER", 1, None, 1),
            ("name", "TEXT", 1, None, 0),
        ]
        mock_cursor.fetchone.side_effect = [
            (42,),  # row count
            # schema
            ("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",),
        ]

        result = get_table_info(mock_cursor, "users")

        assert result["row_count"] == 42
        assert len(result["columns"]) == 2
        assert result["schema"] == ("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

    def test_create_table(self):
        """Test create_table generates correct SQL."""
        mock_cursor = MagicMock()
        columns = [
            {"name": "id", "type": "INTEGER", "constraints": "PRIMARY KEY"},
            {"name": "name", "type": "TEXT", "constraints": "NOT NULL"},
        ]

        sql = create_table(mock_cursor, "users", columns)

        expected_sql = (
            "CREATE TABLE IF NOT EXISTS users " "(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        assert sql == expected_sql
        mock_cursor.execute.assert_called_once_with(expected_sql)

    def test_create_table_no_if_not_exists(self):
        """Test create_table without IF NOT EXISTS."""
        mock_cursor = MagicMock()
        columns = [{"name": "id", "type": "INTEGER"}]

        sql = create_table(mock_cursor, "test", columns, if_not_exists=False)

        assert "IF NOT EXISTS" not in sql

    def test_drop_table(self):
        """Test drop_table generates correct SQL."""
        mock_cursor = MagicMock()

        sql = drop_table(mock_cursor, "old_table")

        expected_sql = "DROP TABLE old_table"
        assert sql == expected_sql
        mock_cursor.execute.assert_called_once_with(expected_sql)
