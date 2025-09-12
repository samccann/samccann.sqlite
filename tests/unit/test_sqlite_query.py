"""Unit tests for sqlite_query module."""

import os
import sqlite3
import sys

from unittest.mock import MagicMock, patch

import pytest


# Add the modules directory to sys.path for importing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../../plugins/modules"),
)

try:
    from sqlite_query import execute_query
except ImportError:
    # Skip tests if module can't be imported
    pytest.skip("Cannot import sqlite_query module", allow_module_level=True)


class TestSqliteQueryFunctions:
    """Test class for sqlite_query utility functions."""

    def test_execute_query_missing_database(self):
        """Test execute_query with missing database file."""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(
                sqlite3.DatabaseError,
                match="Database file does not exist",
            ):
                execute_query("/missing/db.sqlite", "SELECT 1")

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_select(self, mock_connect, mock_exists):
        """Test execute_query with SELECT statement."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = MagicMock()
        mock_row.keys.return_value = ["id", "name"]
        mock_cursor.fetchall.return_value = [mock_row]
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = execute_query(
            "/test/db.sqlite",
            "SELECT id, name FROM users",
        )

        assert result["rowcount"] == 1
        assert "rows" in result
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, name FROM users",
        )

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_with_parameters(self, mock_connect, mock_exists):
        """Test execute_query with parameters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        execute_query(
            "/test/db.sqlite",
            "INSERT INTO users (name) VALUES (?)",
            ["John"],
        )

        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (name) VALUES (?)",
            ["John"],
        )

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_modifying(self, mock_connect, mock_exists):
        """Test execute_query with modifying statement."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = execute_query(
            "/test/db.sqlite",
            "UPDATE users SET name = 'John'",
        )

        assert result["changed"] is True

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_error(self, mock_connect, mock_exists):
        """Test execute_query with database error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("SQL syntax error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(sqlite3.DatabaseError):
            execute_query("/test/db.sqlite", "INVALID SQL")

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_fetch_none(self, mock_connect, mock_exists):
        """Test execute_query with fetch=none."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = execute_query(
            "/test/db.sqlite",
            "SELECT * FROM users",
            fetch="none",
        )

        assert "rows" not in result

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_multiple_statements(self, mock_connect, mock_exists):
        """Test execute_query with multiple statements."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = execute_query(
            "/test/db.sqlite",
            "INSERT INTO users (name) VALUES ('User1'); INSERT INTO users (name) VALUES ('User2');",
        )

        # Should use executescript for multiple statements
        mock_cursor.executescript.assert_called_once()
        mock_cursor.execute.assert_not_called()
        assert result["changed"] is True

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_multiple_statements_with_parameters_error(
        self,
        mock_connect,
        mock_exists,
    ):
        """Test execute_query with multiple statements and parameters should fail."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(
            sqlite3.DatabaseError,
            match="Parameters are not supported with multiple statements",
        ):
            execute_query(
                "/test/db.sqlite",
                "INSERT INTO users (name) VALUES (?); INSERT INTO users (name) VALUES (?);",
                ["User1", "User2"],
            )

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_ddl_changed_logic(self, mock_connect, mock_exists):
        """Test execute_query DDL operations are always marked as changed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0  # DDL operations often return 0
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Test CREATE (DDL)
        result = execute_query(
            "/test/db.sqlite",
            "CREATE INDEX idx_name ON users(name)",
        )
        assert result["changed"] is True  # Should be True even with rowcount=0

        # Test DROP (DDL)
        result = execute_query(
            "/test/db.sqlite",
            "DROP INDEX idx_name",
        )
        assert result["changed"] is True

        # Test ALTER (DDL)
        result = execute_query(
            "/test/db.sqlite",
            "ALTER TABLE users ADD COLUMN age INTEGER",
        )
        assert result["changed"] is True

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_dml_changed_logic(self, mock_connect, mock_exists):
        """Test execute_query DML operations use rowcount for changed logic."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Test INSERT with rowcount > 0
        mock_cursor.rowcount = 1
        result = execute_query(
            "/test/db.sqlite",
            "INSERT INTO users (name) VALUES ('John')",
        )
        assert result["changed"] is True

        # Test UPDATE with rowcount = 0 (no rows affected)
        mock_cursor.rowcount = 0
        result = execute_query(
            "/test/db.sqlite",
            "UPDATE users SET name = 'Jane' WHERE id = 999",
        )
        assert result["changed"] is False

    @patch("os.path.exists", return_value=True)
    @patch("sqlite3.connect")
    def test_execute_query_select_not_changed(self, mock_connect, mock_exists):
        """Test execute_query SELECT operations are never marked as changed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 5  # Even with rowcount > 0
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = execute_query(
            "/test/db.sqlite",
            "SELECT * FROM users",
        )
        assert result["changed"] is False  # SELECT is never changed
