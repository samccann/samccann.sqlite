#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, SQLite Collection Contributors
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible module for managing SQLite databases.

This module provides functionality to create, delete, or check the state of
SQLite databases with support for file permissions and ownership management.
"""

from __future__ import absolute_import, division, print_function


# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = """
---
module: sqlite_db
short_description: Manage SQLite databases
description:
    - Create, delete, or check the state of SQLite databases
    - Can set file permissions and ownership
version_added: "1.0.0"
author:
    - SQLite Collection Contributors (@sqlite-contributors)
options:
    path:
        description:
            - Path to the SQLite database file
        required: true
        type: path
    state:
        description:
            - Whether the database should exist or not
        choices: [ absent, present ]
        default: present
        type: str
    mode:
        description:
            - File permissions for the database file
        type: str
    owner:
        description:
            - Owner of the database file
        type: str
    group:
        description:
            - Group of the database file
        type: str
    backup:
        description:
            - Create a backup before making changes
        type: bool
        default: false
requirements:
    - python >= 3.6
    - sqlite3 (built-in Python module)
notes:
    - This module uses the built-in sqlite3 Python module
    - Database files are created with restrictive permissions by default
"""

EXAMPLES = """
- name: Create SQLite database
  samccann.sqlite.sqlite_db:
    path: /tmp/example.db
    state: present
    mode: '0640'
    owner: myuser
    group: mygroup

- name: Remove SQLite database
  samccann.sqlite.sqlite_db:
    path: /tmp/example.db
    state: absent

- name: Create database with backup
  samccann.sqlite.sqlite_db:
    path: /tmp/production.db
    state: present
    backup: true
"""

RETURN = """
path:
    description: Path to the database file
    returned: always
    type: str
    sample: /tmp/example.db
changed:
    description: Whether the database was changed
    returned: always
    type: bool
    sample: true
size:
    description: Size of the database file in bytes
    returned: when state=present
    type: int
    sample: 8192
backup_file:
    description: Path to the backup file (if backup was created)
    returned: when backup=true and file existed
    type: str
    sample: /tmp/example.db.backup.20240101_120000
"""

import grp
import os
import pwd
import shutil
import sqlite3

from datetime import datetime

from ansible.module_utils.basic import AnsibleModule


def validate_database_path(path):
    """Validate database file path to prevent directory traversal attacks"""
    if not isinstance(path, str):
        raise ValueError(f"Database path must be a string, got {type(path)}")
    
    # Resolve the path to prevent directory traversal
    try:
        resolved_path = os.path.realpath(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"Invalid database path: {str(error)}")
    
    # Check for directory traversal attempts
    if ".." in path or path != resolved_path:
        raise ValueError(f"Directory traversal detected in path: {path}")
    
    # Ensure the path is absolute for security
    if not os.path.isabs(resolved_path):
        raise ValueError(f"Database path must be absolute: {path}")
    
    return resolved_path


def create_database(path):
    """Create an SQLite database file"""
    try:
        conn = sqlite3.connect(path)
        # Simple operation to ensure file is created
        conn.execute("PRAGMA user_version = 1;")
        conn.close()
        return True
    except sqlite3.Error:
        return False


def get_file_size(path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def create_backup(path):
    """Create a backup of the database file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.backup.{timestamp}"
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except OSError:
        return None


def main():  # pylint: disable=too-many-branches
    """Main function for the module"""
    module = AnsibleModule(
        argument_spec={
            "path": {"required": True, "type": "path"},
            "state": {"default": "present", "choices": ["absent", "present"]},
            "mode": {"type": "str"},
            "owner": {"type": "str"},
            "group": {"type": "str"},
            "backup": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
    )

    path = module.params["path"]
    state = module.params["state"]
    mode = module.params["mode"]
    owner = module.params["owner"]
    group = module.params["group"]
    backup = module.params["backup"]

    # Validate database path for security
    try:
        validated_path = validate_database_path(path)
    except ValueError as error:
        module.fail_json(msg=f"Invalid database path: {str(error)}")

    result = {
        "changed": False,
        "path": validated_path,
    }

    # Use validated path for all operations
    path = validated_path
    file_exists = os.path.exists(path)

    # Handle backup if requested and file exists
    backup_file = None
    if backup and file_exists and not module.check_mode:
        backup_file = create_backup(path)
        if backup_file:
            result["backup_file"] = backup_file

    if state == "present":
        if not file_exists:
            if not module.check_mode:
                success = create_database(path)
                if not success:
                    module.fail_json(
                        msg=f"Failed to create database at {path}",
                    )
            result["changed"] = True

        if not module.check_mode and (file_exists or result["changed"]):
            result["size"] = get_file_size(path)

            # Set file permissions
            if mode:
                try:
                    os.chmod(path, int(mode, 8))
                except OSError as error:
                    module.fail_json(
                        msg=f"Failed to set mode {mode}: {str(error)}",
                    )

            # Set ownership (requires appropriate privileges)
            if owner or group:
                try:
                    uid = pwd.getpwnam(owner).pw_uid if owner else -1
                    gid = grp.getgrnam(group).gr_gid if group else -1
                    os.chown(path, uid, gid)
                except (KeyError, OSError) as error:
                    module.fail_json(
                        msg=f"Failed to set ownership: {str(error)}",
                    )

    elif state == "absent":
        if file_exists:
            if not module.check_mode:
                try:
                    os.remove(path)
                except OSError as error:
                    module.fail_json(
                        msg=f"Failed to remove database: {str(error)}",
                    )
            result["changed"] = True

    module.exit_json(**result)


if __name__ == "__main__":
    main()
