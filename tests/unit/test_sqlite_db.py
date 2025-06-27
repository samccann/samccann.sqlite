"""Unit tests for sqlite_db module."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import sqlite3

# Add the modules directory to sys.path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/modules'))

try:
    from sqlite_db import create_database, get_file_size, create_backup
except ImportError:
    # Skip tests if module can't be imported
    pytest.skip("Cannot import sqlite_db module", allow_module_level=True)


class TestSqliteDbFunctions:
    """Test class for sqlite_db utility functions."""

    def test_get_file_size_exists(self):
        """Test get_file_size with existing file."""
        with patch('os.path.getsize', return_value=8192):
            assert get_file_size('/test/db.sqlite') == 8192

    def test_get_file_size_missing(self):
        """Test get_file_size with missing file."""
        with patch('os.path.getsize', side_effect=OSError):
            assert get_file_size('/missing/db.sqlite') == 0

    @patch('sqlite3.connect')
    def test_create_database_success(self, mock_connect):
        """Test successful database creation."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = create_database('/test/new.db')
        
        assert result is True
        mock_connect.assert_called_once_with('/test/new.db')
        mock_conn.execute.assert_called_once_with("PRAGMA user_version = 1;")
        mock_conn.close.assert_called_once()

    @patch('sqlite3.connect')
    def test_create_database_failure(self, mock_connect):
        """Test database creation failure."""
        mock_connect.side_effect = sqlite3.Error("Permission denied")
        
        result = create_database('/test/new.db')
        
        assert result is False

    @patch('shutil.copy2')
    @patch('sqlite_db.datetime')
    def test_create_backup_success(self, mock_datetime, mock_copy):
        """Test successful backup creation."""
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        result = create_backup('/test/db.sqlite')
        
        assert result == '/test/db.sqlite.backup.20240101_120000'
        mock_copy.assert_called_once_with('/test/db.sqlite', '/test/db.sqlite.backup.20240101_120000')

    @patch('shutil.copy2')
    @patch('sqlite_db.datetime')
    def test_create_backup_failure(self, mock_datetime, mock_copy):
        """Test backup creation failure."""
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_copy.side_effect = OSError("Permission denied")
        
        result = create_backup('/test/db.sqlite')
        
        assert result is None 