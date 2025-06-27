"""Unit tests for sqlite_query module."""

import os
import sys
import sqlite3
import pytest
from unittest.mock import patch, MagicMock

# Add the modules directory to sys.path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/modules'))

try:
    from sqlite_query import execute_query
except ImportError:
    # Skip tests if module can't be imported
    pytest.skip("Cannot import sqlite_query module", allow_module_level=True)


class TestSqliteQueryFunctions:
    """Test class for sqlite_query utility functions."""

    def test_execute_query_missing_database(self):
        """Test execute_query with missing database file."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(sqlite3.DatabaseError, match="Database file does not exist"):
                execute_query('/missing/db.sqlite', 'SELECT 1')

    @patch('os.path.exists')
    @patch('sqlite3.connect')
    def test_execute_query_select_all(self, mock_connect, mock_exists):
        """Test execute_query with SELECT and fetch=all."""
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = MagicMock(spec=sqlite3.Row)
        mock_row.keys.return_value = ['id', 'name']
        mock_row.__iter__ = lambda self: iter([1, 'John'])
        
        mock_cursor.fetchall.return_value = [mock_row]
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = execute_query('/test/db.sqlite', 'SELECT id, name FROM users')
        
        assert result['rowcount'] == 1
        assert result['columns'] == ['id', 'name']
        assert result['rows'] == [[1, 'John']]
        assert result['changed'] is False
        mock_cursor.execute.assert_called_once_with('SELECT id, name FROM users')
        mock_conn.commit.assert_called_once()

    @patch('os.path.exists')
    @patch('sqlite3.connect')
    def test_execute_query_with_parameters(self, mock_connect, mock_exists):
        """Test execute_query with parameterized query."""
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = execute_query('/test/db.sqlite', 'INSERT INTO users (name, email) VALUES (?, ?)', 
                             parameters=['John', 'john@example.com'])
        
        mock_cursor.execute.assert_called_once_with('INSERT INTO users (name, email) VALUES (?, ?)', 
                                                   ['John', 'john@example.com'])
        assert result['changed'] is True

    @patch('os.path.exists')
    @patch('sqlite3.connect')
    def test_execute_query_insert_operation(self, mock_connect, mock_exists):
        """Test execute_query with INSERT operation."""
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = execute_query('/test/db.sqlite', 'INSERT INTO users (name) VALUES ("Alice")')
        
        assert result['changed'] is True
        assert result['rowcount'] == 1

    @patch('os.path.exists')
    @patch('sqlite3.connect')
    def test_execute_query_sqlite_error(self, mock_connect, mock_exists):
        """Test execute_query with SQLite error."""
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("SQL syntax error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        with pytest.raises(sqlite3.DatabaseError, match="SQLite error: SQL syntax error"):
            execute_query('/test/db.sqlite', 'INVALID SQL')
        
        mock_conn.rollback.assert_called_once()

    @patch('os.path.exists')
    @patch('sqlite3.connect')
    def test_execute_query_empty_result(self, mock_connect, mock_exists):
        """Test execute_query with empty SELECT result."""
        mock_exists.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = execute_query('/test/db.sqlite', 'SELECT * FROM empty_table')
        
        assert result['rowcount'] == 0
        assert 'columns' not in result
        assert 'rows' not in result 