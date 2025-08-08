# -*- coding: utf-8 -*-

# Copyright: (c) 2024, SQLite Collection Contributors
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Common utilities for SQLite collection modules.

This module provides standardized error handling, validation,
and common functionality across all SQLite collection modules.
"""

import re
import sqlite3


class SQLiteError(Exception):
    """Base exception for SQLite collection operations"""

    pass


class SQLiteValidationError(SQLiteError):
    """Exception for validation errors"""

    pass


class SQLiteConnectionError(SQLiteError):
    """Exception for database connection errors"""

    pass


class SQLiteOperationError(SQLiteError):
    """Exception for database operation errors"""

    pass


def standardize_error_message(operation, error, context=None):
    """
    Standardize error messages across all modules

    Args:
        operation (str): The operation being performed (e.g., 'database creation')
        error (Exception): The original error
        context (dict): Additional context information

    Returns:
        str: Standardized error message
    """
    context = context or {}

    # Base error message format
    base_msg = f"SQLite {operation} failed"

    # Add specific error details
    if isinstance(error, sqlite3.IntegrityError):
        error_type = "Integrity constraint violation"
    elif isinstance(error, sqlite3.OperationalError):
        error_type = "Database operation error"
    elif isinstance(error, sqlite3.DatabaseError):
        error_type = "Database error"
    elif isinstance(error, (OSError, IOError)):
        error_type = "File system error"
    elif isinstance(error, PermissionError):
        error_type = "Permission error"
    else:
        error_type = "Unexpected error"

    # Build detailed message
    detailed_msg = f"{base_msg}: {error_type} - {str(error)}"

    # Add context if provided
    if context:
        context_parts = []
        for key, value in context.items():
            context_parts.append(f"{key}={value}")
        if context_parts:
            detailed_msg += f" (Context: {', '.join(context_parts)})"

    return detailed_msg


def validate_sql_identifier(name, identifier_type="identifier"):
    """
    Validate SQL identifier names (tables, columns, etc.)

    Args:
        name (str): The identifier to validate
        identifier_type (str): Type of identifier for error messages

    Raises:
        SQLiteValidationError: If identifier is invalid

    Returns:
        str: The validated identifier
    """
    if not isinstance(name, str):
        raise SQLiteValidationError(
            f"SQL {identifier_type} must be a string, got {type(name).__name__}",
        )

    if not name:
        raise SQLiteValidationError(f"SQL {identifier_type} cannot be empty")

    # Check basic format
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise SQLiteValidationError(
            f"Invalid SQL {identifier_type}: '{name}'. "
            "Must start with letter or underscore, contain only letters, numbers, and underscores",
        )

    # Check for reserved keywords
    reserved_keywords = {
        "abort",
        "action",
        "add",
        "after",
        "all",
        "alter",
        "analyze",
        "and",
        "as",
        "asc",
        "attach",
        "autoincrement",
        "before",
        "begin",
        "between",
        "by",
        "cascade",
        "case",
        "cast",
        "check",
        "collate",
        "column",
        "commit",
        "conflict",
        "constraint",
        "create",
        "cross",
        "current_date",
        "current_time",
        "current_timestamp",
        "database",
        "default",
        "deferrable",
        "deferred",
        "delete",
        "desc",
        "detach",
        "distinct",
        "drop",
        "each",
        "else",
        "end",
        "escape",
        "except",
        "exclusive",
        "exists",
        "explain",
        "fail",
        "for",
        "foreign",
        "from",
        "full",
        "glob",
        "group",
        "having",
        "if",
        "ignore",
        "immediate",
        "in",
        "index",
        "indexed",
        "initially",
        "inner",
        "insert",
        "instead",
        "intersect",
        "into",
        "is",
        "isnull",
        "join",
        "key",
        "left",
        "like",
        "limit",
        "match",
        "natural",
        "no",
        "not",
        "notnull",
        "null",
        "of",
        "offset",
        "on",
        "or",
        "order",
        "outer",
        "plan",
        "pragma",
        "primary",
        "query",
        "raise",
        "recursive",
        "references",
        "regexp",
        "reindex",
        "release",
        "rename",
        "replace",
        "restrict",
        "right",
        "rollback",
        "row",
        "savepoint",
        "select",
        "set",
        "table",
        "temp",
        "temporary",
        "then",
        "to",
        "transaction",
        "trigger",
        "union",
        "unique",
        "update",
        "using",
        "vacuum",
        "values",
        "view",
        "virtual",
        "when",
        "where",
        "with",
        "without",
    }

    if name.lower() in reserved_keywords:
        raise SQLiteValidationError(
            f"SQL {identifier_type} '{name}' is a reserved keyword and cannot be used",
        )

    return name


def safe_execute_with_retry(cursor, query, parameters=None, max_retries=3, retry_delay=0.1):
    """
    Execute SQL query with retry logic for transient errors

    Args:
        cursor: SQLite cursor object
        query (str): SQL query to execute
        parameters (list): Query parameters
        max_retries (int): Maximum number of retries
        retry_delay (float): Delay between retries in seconds

    Returns:
        cursor: The cursor after execution

    Raises:
        SQLiteOperationError: If all retries fail
    """
    import time

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.OperationalError as e:
            last_error = e
            error_msg = str(e).lower()

            # Only retry for specific transient errors
            if "database is locked" in error_msg or "busy" in error_msg:
                if attempt < max_retries:
                    time.sleep(retry_delay * (2**attempt))  # Exponential backoff
                    continue

            # Re-raise non-transient errors immediately
            raise SQLiteOperationError(
                standardize_error_message(
                    "query execution",
                    e,
                    {"query": query[:100], "attempt": attempt + 1},
                ),
            )
        except Exception as e:
            raise SQLiteOperationError(
                standardize_error_message(
                    "query execution",
                    e,
                    {"query": query[:100], "attempt": attempt + 1},
                ),
            )

    # All retries failed
    raise SQLiteOperationError(
        standardize_error_message(
            "query execution",
            last_error,
            {"query": query[:100], "max_retries": max_retries, "final_attempt": True},
        ),
    )


def validate_database_path(path):
    """
    Validate database file path for security

    Args:
        path (str): Database file path

    Returns:
        str: Validated absolute path

    Raises:
        SQLiteValidationError: If path is invalid or insecure
    """
    import os

    if not isinstance(path, str):
        raise SQLiteValidationError(
            f"Database path must be a string, got {type(path).__name__}",
        )

    if not path:
        raise SQLiteValidationError("Database path cannot be empty")

    # Resolve the path to prevent directory traversal
    try:
        resolved_path = os.path.realpath(path)
    except (OSError, ValueError) as error:
        raise SQLiteValidationError(f"Invalid database path: {str(error)}")

    # Check for directory traversal attempts
    if ".." in path:
        raise SQLiteValidationError(f"Directory traversal detected in path: {path}")

    # Ensure the path is absolute for security
    if not os.path.isabs(resolved_path):
        raise SQLiteValidationError(f"Database path must be absolute: {path}")

    return resolved_path


def get_connection_with_pragmas(db_path, pragmas=None):
    """
    Get SQLite connection with standard pragmas applied

    Args:
        db_path (str): Path to database file
        pragmas (dict): Additional PRAGMA settings

    Returns:
        sqlite3.Connection: Database connection

    Raises:
        SQLiteConnectionError: If connection fails
    """
    pragmas = pragmas or {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Apply default pragmas for better reliability
        default_pragmas = {
            "foreign_keys": "ON",
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "temp_store": "MEMORY",
            "mmap_size": "268435456",  # 256MB
        }

        # Merge with user-provided pragmas (user pragmas take precedence)
        all_pragmas = {**default_pragmas, **pragmas}

        for pragma, value in all_pragmas.items():
            cursor.execute(f"PRAGMA {pragma} = {value}")

        return conn

    except sqlite3.Error as e:
        raise SQLiteConnectionError(
            standardize_error_message(
                "database connection",
                e,
                {"database_path": db_path},
            ),
        )
