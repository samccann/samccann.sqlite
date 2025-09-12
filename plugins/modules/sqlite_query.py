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
            - Supports multiple statements separated by semicolons
            - Parameters are not supported with multiple statements
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

- name: Execute multiple statements in transaction
  samccann.sqlite.sqlite_query:
    db: /tmp/example.db
    query: |
      INSERT INTO users (name, email) VALUES ('User1', 'user1@example.com');
      INSERT INTO users (name, email) VALUES ('User2', 'user2@example.com');
      UPDATE users SET active = 1 WHERE name LIKE 'User%';
    transaction: true
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
    description: Whether the database was modified. DDL always returns true.
    returned: always
    type: bool
    sample: true
"""

import os
import sqlite3

from ansible.module_utils.basic import AnsibleModule


def execute_query(
    db_path,
    query,
    parameters=None,
    fetch="all",
    transaction=True,
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

        # Execute query - handle multiple statements
        # Check if query contains multiple statements (semicolon-separated)
        statements = [stmt.strip() for stmt in query.split(";") if stmt.strip()]

        if len(statements) > 1:
            # Multiple statements - use executescript (doesn't support parameters)
            if parameters:
                raise sqlite3.DatabaseError(
                    "Parameters are not supported with multiple statements",
                )
            cursor.executescript(query)
            results["rowcount"] = cursor.rowcount
        else:
            # Single statement - use execute (supports parameters)
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
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
        dml_keywords = ["insert", "update", "delete"]
        ddl_keywords = ["create", "drop", "alter"]

        query_lower = query.lower().strip()

        # Check if we have multiple statements
        statements = [stmt.strip() for stmt in query.split(";") if stmt.strip()]

        if len(statements) > 1:
            # For multiple statements, check if any statement is modifying
            is_any_modifying = False
            for stmt in statements:
                stmt_lower = stmt.lower().strip()
                if any(keyword in stmt_lower for keyword in dml_keywords + ddl_keywords):
                    is_any_modifying = True
                    break
            results["changed"] = is_any_modifying
        else:
            # Single statement logic
            is_dml = any(keyword in query_lower for keyword in dml_keywords)
            is_ddl = any(keyword in query_lower for keyword in ddl_keywords)

            # For DML operations, check rowcount; for DDL operations, assume changed if successful
            if is_dml:
                results["changed"] = cursor.rowcount > 0
            elif is_ddl:
                results["changed"] = True  # DDL operations always change the database schema
            else:
                results["changed"] = False  # SELECT and other read-only operations

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
        },
        supports_check_mode=False,  # SQL queries can't be safely checked
    )

    db_path = module.params["db"]
    query = module.params["query"]
    parameters = module.params["parameters"]
    fetch = module.params["fetch"]
    transaction = module.params["transaction"]

    try:
        result = execute_query(db_path, query, parameters, fetch, transaction)
        result["query"] = query
        result.setdefault("changed", False)
        module.exit_json(**result)
    except sqlite3.Error as error:
        module.fail_json(msg=str(error))


if __name__ == "__main__":
    main()
