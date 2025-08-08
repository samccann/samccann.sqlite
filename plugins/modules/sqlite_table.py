#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, SQLite Collection Contributors
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible module for managing SQLite database tables.

This module provides functionality to create, drop, or inspect SQLite
database tables with support for complex table definitions and schema
information.
"""

from __future__ import absolute_import, division, print_function


# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: sqlite_table
short_description: Manage SQLite database tables
description:
    - Create, drop, or inspect SQLite database tables
    - Get table schema information and statistics
    - Support for complex table definitions
version_added: "1.0.0"
author:
    - SQLite Collection Contributors (@sqlite-contributors)
options:
    db:
        description:
            - Path to the SQLite database file
        required: true
        type: path
    name:
        description:
            - Name of the table to manage
        required: true
        type: str
    state:
        description:
            - Whether the table should exist or not
        choices: [ absent, present ]
        default: present
        type: str
    columns:
        description:
            - Column definitions for table creation
            - Each column should be a dict with 'name', 'type', and optional
              'constraints'
        type: list
        elements: dict
    if_not_exists:
        description:
            - Use IF NOT EXISTS when creating table
        type: bool
        default: true
    cascade:
        description:
            - Use CASCADE when dropping table (affects foreign keys)
        type: bool
        default: false
    gather_info:
        description:
            - Gather and return detailed information about the table
        type: bool
        default: false
requirements:
    - python >= 3.6
    - sqlite3 (built-in Python module)
"""

EXAMPLES = """
- name: Create users table
  samccann.sqlite.sqlite_table:
    db: /tmp/example.db
    name: users
    state: present
    columns:
      - name: id
        type: INTEGER
        constraints: PRIMARY KEY AUTOINCREMENT
      - name: username
        type: TEXT
        constraints: NOT NULL UNIQUE
      - name: email
        type: TEXT
        constraints: NOT NULL
      - name: created_at
        type: TIMESTAMP
        constraints: DEFAULT CURRENT_TIMESTAMP

- name: Get table information
  samccann.sqlite.sqlite_table:
    db: /tmp/example.db
    name: users
    state: present
    gather_info: true
  register: table_info

- name: Drop table
  samccann.sqlite.sqlite_table:
    db: /tmp/example.db
    name: old_table
    state: absent
"""

RETURN = """
table:
    description: Name of the table
    returned: always
    type: str
    sample: users
changed:
    description: Whether the table was changed
    returned: always
    type: bool
    sample: true
exists:
    description: Whether the table exists
    returned: always
    type: bool
    sample: true
columns:
    description: Table column information
    returned: when gather_info=true
    type: list
    sample: [{"name": "id", "type": "INTEGER", "notnull": 1, "pk": 1}]
row_count:
    description: Number of rows in the table
    returned: when gather_info=true and table exists
    type: int
    sample: 42
schema:
    description: CREATE TABLE statement for the table
    returned: when gather_info=true and table exists
    type: str
    sample: "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
"""

import os
import re
import sqlite3

from ansible.module_utils.basic import AnsibleModule


def validate_sql_identifier(name):
    """Validate SQL identifier to prevent injection attacks"""
    if not isinstance(name, str):
        raise ValueError(f"SQL identifier must be a string, got {type(name)}")
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    
    # Check for reserved keywords (basic set)
    reserved_keywords = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'table', 'index', 'view', 'trigger', 'database', 'schema',
        'where', 'order', 'group', 'having', 'union', 'join'
    }
    
    if name.lower() in reserved_keywords:
        raise ValueError(f"SQL identifier cannot be a reserved keyword: {name}")


def table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_table_info(cursor, table_name):
    """Get detailed table information"""
    info = {}

    # Get column information
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    info["columns"] = [dict(zip([col[0] for col in cursor.description], row)) for row in columns]

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    info["row_count"] = cursor.fetchone()[0]

    # Get table schema
    cursor.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type='table' AND name=?
    """,
        (table_name,),
    )
    result = cursor.fetchone()
    info["schema"] = result[0] if result else None

    return info


def create_table(cursor, table_name, columns, if_not_exists=True):
    """Create table with specified columns"""
    if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""

    # Validate table name
    validate_sql_identifier(table_name)
    
    # Build column definitions
    column_defs = []
    for col in columns:
        # Validate column name and type
        validate_sql_identifier(col['name'])
        validate_sql_identifier(col['type'])
        
        col_def = f"{col['name']} {col['type']}"
        if "constraints" in col and col["constraints"]:
            col_def += f" {col['constraints']}"
        column_defs.append(col_def)

    columns_sql = ", ".join(column_defs)
    sql = f"CREATE TABLE {if_not_exists_clause}{table_name} ({columns_sql})"

    cursor.execute(sql)
    return sql


def drop_table(cursor, table_name, cascade=False):
    """Drop table"""
    # Validate table name
    validate_sql_identifier(table_name)
    
    # SQLite doesn't support CASCADE, but we can check for it
    if cascade:
        # This is more for compatibility - SQLite handles FK constraints
        # differently
        pass

    sql = f"DROP TABLE {table_name}"
    cursor.execute(sql)
    return sql


def main():  # pylint: disable=too-many-branches
    """Main function for the module"""
    module = AnsibleModule(
        argument_spec={
            "db": {"required": True, "type": "path"},
            "name": {"required": True, "type": "str"},
            "state": {"default": "present", "choices": ["absent", "present"]},
            "columns": {"type": "list", "elements": "dict"},
            "if_not_exists": {"type": "bool", "default": True},
            "cascade": {"type": "bool", "default": False},
            "gather_info": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["columns"]),
        ],
    )

    db_path = module.params["db"]
    table_name = module.params["name"]
    state = module.params["state"]
    columns = module.params["columns"]
    if_not_exists = module.params["if_not_exists"]
    cascade = module.params["cascade"]
    gather_info = module.params["gather_info"]

    if not os.path.exists(db_path):
        module.fail_json(msg=f"Database file does not exist: {db_path}")

    result = {
        "changed": False,
        "table": table_name,
    }

    conn = None
    cursor = None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Validate table name early
        try:
            validate_sql_identifier(table_name)
        except ValueError as error:
            module.fail_json(msg=f"Invalid table name: {str(error)}")

        exists = table_exists(cursor, table_name)
        result["exists"] = exists

        # Gather information if requested
        if gather_info and exists:
            info = get_table_info(cursor, table_name)
            result.update(info)

        if state == "present":
            if not exists:
                if not module.check_mode:
                    create_table(cursor, table_name, columns, if_not_exists)
                    conn.commit()
                result["changed"] = True
                result["exists"] = True

        elif state == "absent":
            if exists:
                if not module.check_mode:
                    drop_table(cursor, table_name, cascade)
                    conn.commit()
                result["changed"] = True
                result["exists"] = False

    except sqlite3.Error as error:
        module.fail_json(msg=f"SQLite error: {str(error)}")
    except OSError as error:
        module.fail_json(msg=f"OS Error: {str(error)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
