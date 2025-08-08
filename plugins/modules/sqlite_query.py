#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, SQLite Collection Contributors
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible module for executing SQL queries on SQLite databases.

This module provides functionality to execute SELECT, INSERT, UPDATE,
DELETE and other SQL statements with support for parameterized queries and
result fetching.
"""

from __future__ import absolute_import, division, print_function


# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: sqlite_query
short_description: Execute SQL queries on SQLite databases
description:
    - Execute SELECT, INSERT, UPDATE, DELETE and other SQL statements
    - Support for parameterized queries to prevent SQL injection
    - Return query results and execution statistics
version_added: "1.0.0"
author:
    - SQLite Collection Contributors (@sqlite-contributors)
options:
    db:
        description:
            - Path to the SQLite database file
        required: true
        type: path
    query:
        description:
            - SQL query to execute
        required: true
        type: str
    parameters:
        description:
            - Parameters for parameterized queries
            - Use ? placeholders in query and provide values here
        type: list
        elements: raw
    fetch:
        description:
            - How to fetch results for SELECT queries
        choices: [ all, one, none ]
        default: all
        type: str
    transaction:
        description:
            - Whether to execute in a transaction
        type: bool
        default: true
    timeout:
        description:
            - Query timeout in seconds
            - Set to 0 for no timeout (use with caution)
        type: int
        default: 30
requirements:
    - python >= 3.6
    - sqlite3 (built-in Python module)
"""

EXAMPLES = """
- name: Create a table
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: |
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
      )

- name: Insert data with parameters
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: "INSERT INTO users (name, email) VALUES (?, ?)"
    parameters:
      - "John Doe"
      - "john@example.com"

- name: Select all users
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: "SELECT * FROM users"
    fetch: all
  register: users_result

- name: Update with transaction
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: "UPDATE users SET email = ? WHERE name = ?"
    parameters:
      - "newemail@example.com"
      - "John Doe"
    transaction: true

- name: Get table count
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: "SELECT COUNT(*) as total FROM users"
    fetch: one
  register: count_result
"""

RETURN = """
query:
    description: The executed SQL query
    returned: always
    type: str
    sample: "SELECT * FROM users"
rowcount:
    description: Number of rows affected by the query
    returned: always
    type: int
    sample: 3
rows:
    description: Query results (for SELECT statements)
    returned: when fetch != 'none' and query returns data
    type: list
    sample: [
        ["1", "John Doe", "john@example.com"],
        ["2", "Jane Smith", "jane@example.com"],
    ]
columns:
    description: Column names from the query result
    returned: when fetch != 'none' and query returns data
    type: list
    sample: ["id", "name", "email"]
changed:
    description: Whether the database was modified
    returned: always
    type: bool
    sample: true
"""

import os
import sqlite3
import threading

from ansible.module_utils.basic import AnsibleModule


class QueryTimeout(Exception):
    """Exception raised when query times out"""

    pass


def execute_query_with_timeout(cursor, query, parameters, timeout):
    """Execute query with timeout using threading"""
    result = {"success": False, "error": None}

    def target():
        try:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            result["success"] = True
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout if timeout > 0 else None)

    if thread.is_alive():
        # Query is still running, timeout occurred
        raise QueryTimeout(f"Query timed out after {timeout} seconds")

    # Check if an error occurred during execution
    error = result.get("error")
    if error is not None:
        raise error

    return result["success"]


def execute_query(
    db_path,
    query,
    parameters=None,
    fetch="all",
    transaction=True,
    timeout=30,
):  # pylint: disable=too-many-branches,too-many-statements
    """Execute SQL query on SQLite database"""
    if not os.path.exists(db_path):
        raise sqlite3.DatabaseError(
            f"Database file does not exist: {db_path}",
        )

    conn = None
    cursor = None
    results = {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable row factory to get column names
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Execute query with timeout
        execute_query_with_timeout(cursor, query, parameters, timeout)

        results["rowcount"] = cursor.rowcount

        # Fetch results based on fetch parameter
        if fetch != "none":
            query_lower = query.lower().strip()
            if query_lower.startswith("select") or "returning" in query_lower:
                if fetch == "all":
                    rows = cursor.fetchall()
                elif fetch == "one":
                    rows = cursor.fetchone()
                    rows = [rows] if rows else []
                else:
                    rows = []

                if rows:
                    # Convert Row objects to lists and get column names
                    if isinstance(rows[0], sqlite3.Row):
                        results["columns"] = list(rows[0].keys())
                        results["rows"] = [list(row) for row in rows]
                    else:
                        results["rows"] = rows

        # Determine if this was a modifying query
        modifying_keywords = [
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
        ]
        is_modifying = any(keyword in query.lower() for keyword in modifying_keywords)
        results["changed"] = is_modifying and cursor.rowcount > 0

        if transaction:
            conn.commit()

    except sqlite3.Error as error:
        if conn and transaction:
            conn.rollback()
        raise sqlite3.DatabaseError(f"SQLite error: {str(error)}") from error
    except Exception as error:
        if conn and transaction:
            conn.rollback()
        raise error
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return results


def main():
    """Main function for the module"""
    module = AnsibleModule(
        argument_spec={
            "db": {"required": True, "type": "path"},
            "query": {"required": True, "type": "str"},
            "parameters": {"type": "list", "elements": "raw"},
            "fetch": {"default": "all", "choices": ["all", "one", "none"]},
            "transaction": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 30},
        },
        supports_check_mode=False,  # SQL queries can't be safely checked
    )

    db_path = module.params["db"]
    query = module.params["query"]
    parameters = module.params["parameters"]
    fetch = module.params["fetch"]
    transaction = module.params["transaction"]
    timeout = module.params["timeout"]

    try:
        result = execute_query(db_path, query, parameters, fetch, transaction, timeout)
        result["query"] = query
        result.setdefault("changed", False)
        module.exit_json(**result)
    except (sqlite3.Error, QueryTimeout) as error:
        module.fail_json(msg=str(error))


if __name__ == "__main__":
    main()
