"""Unit tests for sqlite_backup module."""

import os
import sqlite3
import sys

from unittest.mock import MagicMock, mock_open, patch

import pytest


# Add the modules directory to sys.path for importing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../../plugins/modules"),
)

try:
    from sqlite_backup import (
        backup_database,
        get_file_size,
        is_compressed_file,
        restore_database,
        verify_sqlite_db,
    )
except ImportError:
    # Skip tests if module can't be imported
    pytest.skip("Cannot import sqlite_backup module", allow_module_level=True)


class TestSqliteBackupFunctions:
    """Test class for sqlite_backup utility functions."""

    def test_get_file_size_exists(self):
        """Test get_file_size with existing file."""
        with patch("os.path.getsize", return_value=1024):
            assert get_file_size("/test/file.db") == 1024

    def test_get_file_size_missing(self):
        """Test get_file_size with missing file."""
        with patch("os.path.getsize", side_effect=OSError):
            assert get_file_size("/missing/file.db") == 0

    @patch("sqlite3.connect")
    def test_verify_sqlite_db_valid(self, mock_connect):
        """Test verify_sqlite_db with valid database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["ok"]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        assert verify_sqlite_db("/test/db.sqlite") is True
        mock_cursor.execute.assert_called_once_with("PRAGMA integrity_check")
        mock_conn.close.assert_called_once()

    @patch("sqlite3.connect")
    def test_verify_sqlite_db_invalid(self, mock_connect):
        """Test verify_sqlite_db with invalid database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["error"]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        assert verify_sqlite_db("/test/db.sqlite") is False

    @patch("sqlite3.connect")
    def test_verify_sqlite_db_exception(self, mock_connect):
        """Test verify_sqlite_db with database exception."""
        mock_connect.side_effect = sqlite3.Error("Database error")
        assert verify_sqlite_db("/test/db.sqlite") is False

    def test_is_compressed_file_true(self):
        """Test is_compressed_file with gzip file."""
        with patch("builtins.open", mock_open(read_data=b"\x1f\x8b")):
            assert is_compressed_file("/test/file.gz") is True

    def test_is_compressed_file_false(self):
        """Test is_compressed_file with regular file."""
        with patch("builtins.open", mock_open(read_data=b"regular")):
            assert is_compressed_file("/test/file.db") is False

    def test_is_compressed_file_exception(self):
        """Test is_compressed_file with file error."""
        with patch("builtins.open", side_effect=OSError):
            assert is_compressed_file("/missing/file.db") is False

    @patch("time.time")
    @patch("shutil.copy2")
    def test_backup_database_uncompressed(self, mock_copy, mock_time):
        """Test backup_database without compression."""
        mock_time.side_effect = [1000.0, 1002.5]  # 2.5 second operation

        result = backup_database(
            "/src/db.sqlite",
            "/dest/backup.db",
            compress=False,
        )

        assert result == 2.5
        mock_copy.assert_called_once_with("/src/db.sqlite", "/dest/backup.db")

    @patch("time.time")
    @patch("gzip.open")
    @patch("builtins.open")
    @patch("shutil.copyfileobj")
    def test_backup_database_compressed(
        self,
        mock_copyfileobj,
        mock_open_file,
        mock_gzip_open,
        mock_time,
    ):
        """Test backup_database with compression."""
        mock_time.side_effect = [1000.0, 1003.0]  # 3.0 second operation
        mock_src = MagicMock()
        mock_dest = MagicMock()
        mock_open_file.return_value.__enter__.return_value = mock_src
        mock_gzip_open.return_value.__enter__.return_value = mock_dest

        result = backup_database(
            "/src/db.sqlite",
            "/dest/backup.db.gz",
            compress=True,
        )

        assert result == 3.0
        mock_open_file.assert_called_once_with("/src/db.sqlite", "rb")
        mock_gzip_open.assert_called_once_with("/dest/backup.db.gz", "wb")
        mock_copyfileobj.assert_called_once_with(mock_src, mock_dest)

    @patch("time.time")
    @patch("gzip.open")
    @patch("builtins.open")
    @patch("shutil.copyfileobj")
    def test_restore_database_from_compressed(
        self,
        mock_copyfileobj,
        mock_open_file,
        mock_gzip_open,
        mock_time,
    ):
        """Test restore_database from compressed backup."""
        mock_time.side_effect = [1000.0, 1002.0]  # 2.0 second operation
        mock_src = MagicMock()
        mock_dest = MagicMock()
        mock_gzip_open.return_value.__enter__.return_value = mock_src
        mock_open_file.return_value.__enter__.return_value = mock_dest

        result = restore_database(
            "/backup/db.gz",
            "/restore/db.sqlite",
            compressed=True,
        )

        assert result == 2.0
        mock_gzip_open.assert_called_once_with("/backup/db.gz", "rb")
        mock_open_file.assert_called_once_with("/restore/db.sqlite", "wb")
        mock_copyfileobj.assert_called_once_with(mock_src, mock_dest)

    @patch("time.time")
    @patch("shutil.copy2")
    def test_restore_database_uncompressed(self, mock_copy, mock_time):
        """Test restore_database from uncompressed backup."""
        mock_time.side_effect = [1000.0, 1001.5]  # 1.5 second operation

        result = restore_database(
            "/backup/db.sqlite",
            "/restore/db.sqlite",
            compressed=False,
        )

        assert result == 1.5
        mock_copy.assert_called_once_with(
            "/backup/db.sqlite",
            "/restore/db.sqlite",
        )
