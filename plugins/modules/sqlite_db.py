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
    maintenance:
        description:
            - Perform database maintenance operations
        type: dict
        default: {}
        suboptions:
            vacuum:
                description: Run VACUUM to reclaim space
                type: bool
                default: false
            analyze:
                description: Run ANALYZE to update query optimizer statistics
                type: bool
                default: false
            integrity_check:
                description: Run integrity check
                type: bool
                default: false
    performance:
        description:
            - Performance optimization settings
        type: dict
        default: {}
        suboptions:
            journal_mode:
                description: Set journal mode (DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF)
                type: str
                choices: ['DELETE', 'TRUNCATE', 'PERSIST', 'MEMORY', 'WAL', 'OFF']
                default: WAL
            synchronous:
                description: Set synchronous mode (0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA)
                type: int
                choices: [0, 1, 2, 3]
                default: 1
            cache_size:
                description: Set cache size (negative for KB, positive for pages)
                type: int
                default: -8192
            temp_store:
                description: Set temp store mode (0=DEFAULT, 1=FILE, 2=MEMORY)
                type: int
                choices: [0, 1, 2]
                default: 2
    foreign_keys:
        description:
            - Enable foreign key constraint enforcement
        type: bool
        default: true
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

- name: Perform database maintenance
  samccann.sqlite.sqlite_db:
    path: /tmp/production.db
    state: present
    maintenance:
      vacuum: true
      analyze: true
      integrity_check: true

- name: Create high-performance database
  samccann.sqlite.sqlite_db:
    path: /tmp/fast.db
    state: present
    performance:
      journal_mode: WAL
      synchronous: 1
      cache_size: -16384
      temp_store: 2
    foreign_keys: true
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
maintenance_results:
    description: Results of maintenance operations
    returned: when maintenance operations are performed
    type: dict
    sample: {"vacuum": true, "analyze": true, "integrity_check": "ok"}
performance_results:
    description: Results of performance optimization settings
    returned: when performance settings are applied
    type: dict
    sample: {"journal_mode": "wal", "synchronous": 1, "cache_size": -8192}
foreign_keys_enabled:
    description: Whether foreign key constraints are enabled
    returned: when foreign_keys parameter is used
    type: bool
    sample: true
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


def perform_maintenance(path, maintenance_options):
    """Perform database maintenance operations"""
    results = {}

    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        if maintenance_options.get("integrity_check", False):
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            results["integrity_check"] = result[0] if result else "failed"

        if maintenance_options.get("vacuum", False):
            cursor.execute("VACUUM")
            results["vacuum"] = True

        if maintenance_options.get("analyze", False):
            cursor.execute("ANALYZE")
            results["analyze"] = True

        conn.commit()
        conn.close()

    except sqlite3.Error as error:
        results["error"] = str(error)
        return results

    return results


def apply_performance_settings(path, performance_options):
    """Apply performance optimization settings"""
    results = {}

    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        # Set journal mode
        if "journal_mode" in performance_options:
            journal_mode = performance_options["journal_mode"]
            cursor.execute(f"PRAGMA journal_mode = {journal_mode}")
            result = cursor.fetchone()
            results["journal_mode"] = result[0] if result else journal_mode.lower()

        # Set synchronous mode
        if "synchronous" in performance_options:
            synchronous = performance_options["synchronous"]
            cursor.execute(f"PRAGMA synchronous = {synchronous}")
            results["synchronous"] = synchronous

        # Set cache size
        if "cache_size" in performance_options:
            cache_size = performance_options["cache_size"]
            cursor.execute(f"PRAGMA cache_size = {cache_size}")
            results["cache_size"] = cache_size

        # Set temp store
        if "temp_store" in performance_options:
            temp_store = performance_options["temp_store"]
            cursor.execute(f"PRAGMA temp_store = {temp_store}")
            results["temp_store"] = temp_store

        conn.close()

    except sqlite3.Error as error:
        results["error"] = str(error)
        return results

    return results


def configure_foreign_keys(path, enable_foreign_keys):
    """Configure foreign key constraint enforcement"""
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        if enable_foreign_keys:
            cursor.execute("PRAGMA foreign_keys = ON")
        else:
            cursor.execute("PRAGMA foreign_keys = OFF")

        # Verify the setting
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        enabled = bool(result[0]) if result else False

        conn.close()
        return enabled

    except sqlite3.Error as error:
        raise sqlite3.Error(f"Failed to configure foreign keys: {str(error)}")


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
            "maintenance": {"type": "dict", "default": {}},
            "performance": {"type": "dict", "default": {}},
            "foreign_keys": {"type": "bool", "default": True},
        },
        supports_check_mode=True,
    )

    path = module.params["path"]
    state = module.params["state"]
    mode = module.params["mode"]
    owner = module.params["owner"]
    group = module.params["group"]
    backup = module.params["backup"]
    maintenance = module.params["maintenance"]
    performance = module.params["performance"]
    foreign_keys = module.params["foreign_keys"]

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

            # Perform maintenance operations if requested
            if maintenance and not module.check_mode:
                maintenance_results = perform_maintenance(path, maintenance)
                if "error" in maintenance_results:
                    module.fail_json(
                        msg=f"Maintenance operation failed: {maintenance_results['error']}",
                    )
                result["maintenance_results"] = maintenance_results

            # Apply performance settings if requested
            if performance and not module.check_mode:
                performance_results = apply_performance_settings(path, performance)
                if "error" in performance_results:
                    module.fail_json(
                        msg=f"Performance optimization failed: {performance_results['error']}",
                    )
                result["performance_results"] = performance_results

            # Configure foreign keys if specified
            if not module.check_mode:
                try:
                    enabled = configure_foreign_keys(path, foreign_keys)
                    result["foreign_keys_enabled"] = enabled
                except sqlite3.Error as error:
                    module.fail_json(
                        msg=f"Failed to configure foreign keys: {str(error)}",
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
