#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, SQLite Collection Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Ansible module for SQLite database backup and restore operations.

This module provides functionality to backup, restore, and verify SQLite databases
with support for compression and integrity checking.
"""

from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type

DOCUMENTATION = '''
---
module: sqlite_backup
short_description: Backup and restore SQLite databases
description:
    - Create backups of SQLite databases
    - Restore databases from backup files
    - Support for compressed backups
    - Validate backup integrity
version_added: "1.0.0"
author:
    - SQLite Collection Contributors (@sqlite-contributors)
options:
    src:
        description:
            - Source database file path
        required: true
        type: path
    dest:
        description:
            - Destination backup file path
        required: true
        type: path
    operation:
        description:
            - Operation to perform
        choices: [ backup, restore, verify ]
        default: backup
        type: str
    compress:
        description:
            - Compress the backup file (requires gzip module)
        type: bool
        default: false
    overwrite:
        description:
            - Overwrite destination file if it exists
        type: bool
        default: false
    verify_backup:
        description:
            - Verify backup integrity after creation
        type: bool
        default: true
requirements:
    - python >= 3.6
    - sqlite3 (built-in Python module)
    - gzip (built-in Python module, optional for compression)
'''

EXAMPLES = '''
- name: Create database backup
  cursor.sqlite.sqlite_backup:
    src: /var/lib/app/production.db
    dest: /backup/production_backup.db
    operation: backup
    verify_backup: true

- name: Create compressed backup
  cursor.sqlite.sqlite_backup:
    src: /var/lib/app/production.db
    dest: /backup/production_backup.db.gz
    operation: backup
    compress: true

- name: Restore database from backup
  cursor.sqlite.sqlite_backup:
    src: /backup/production_backup.db
    dest: /var/lib/app/restored.db
    operation: restore
    overwrite: true

- name: Verify backup integrity
  cursor.sqlite.sqlite_backup:
    src: /backup/production_backup.db
    dest: /dev/null
    operation: verify
'''

RETURN = '''
src:
    description: Source file path
    returned: always
    type: str
    sample: /var/lib/app/production.db
dest:
    description: Destination file path
    returned: always
    type: str
    sample: /backup/production_backup.db
operation:
    description: Operation performed
    returned: always
    type: str
    sample: backup
changed:
    description: Whether any changes were made
    returned: always
    type: bool
    sample: true
src_size:
    description: Size of source file in bytes
    returned: always
    type: int
    sample: 1048576
dest_size:
    description: Size of destination file in bytes
    returned: when dest file exists
    type: int
    sample: 1048576
compressed:
    description: Whether the backup is compressed
    returned: always
    type: bool
    sample: false
verified:
    description: Whether backup was verified (if verify_backup=true)
    returned: when operation=backup and verify_backup=true
    type: bool
    sample: true
backup_time:
    description: Time taken for backup operation in seconds
    returned: when operation=backup
    type: float
    sample: 2.34
'''

import os
import sqlite3
import shutil
import time
import gzip
import tempfile
from ansible.module_utils.basic import AnsibleModule


def get_file_size(path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def verify_sqlite_db(db_path):
    """Verify SQLite database integrity"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        return result[0] == 'ok'
    except sqlite3.Error:
        return False


def backup_database(src_path, dest_path, compress=False):
    """Backup SQLite database"""
    start_time = time.time()

    if compress:
        with open(src_path, 'rb') as src_file:
            with gzip.open(dest_path, 'wb') as dest_file:
                shutil.copyfileobj(src_file, dest_file)
    else:
        shutil.copy2(src_path, dest_path)

    end_time = time.time()
    return end_time - start_time


def restore_database(src_path, dest_path, compressed=False):
    """Restore SQLite database from backup"""
    start_time = time.time()

    if compressed:
        with gzip.open(src_path, 'rb') as src_file:
            with open(dest_path, 'wb') as dest_file:
                shutil.copyfileobj(src_file, dest_file)
    else:
        shutil.copy2(src_path, dest_path)

    end_time = time.time()
    return end_time - start_time


def is_compressed_file(file_path):
    """Check if file is gzip compressed"""
    try:
        with open(file_path, 'rb') as file_handle:
            return file_handle.read(2) == b'\x1f\x8b'
    except OSError:
        return False


def main():  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Main function for the module"""
    module = AnsibleModule(
        argument_spec={
            "src": {"required": True, "type": 'path'},
            "dest": {"required": True, "type": 'path'},
            "operation": {"default": 'backup', "choices": ['backup', 'restore', 'verify']},
            "compress": {"type": 'bool', "default": False},
            "overwrite": {"type": 'bool', "default": False},
            "verify_backup": {"type": 'bool', "default": True}
        },
        supports_check_mode=True
    )

    src_path = module.params['src']
    dest_path = module.params['dest']
    operation = module.params['operation']
    compress = module.params['compress']
    overwrite = module.params['overwrite']
    verify_backup = module.params['verify_backup']

    result = {
        "changed": False,
        "src": src_path,
        "dest": dest_path,
        "operation": operation,
        "compressed": compress
    }

    # Check if source file exists
    if not os.path.exists(src_path) and operation != 'verify':
        module.fail_json(msg=f"Source file does not exist: {src_path}")

    # Get source file size
    if os.path.exists(src_path):
        result['src_size'] = get_file_size(src_path)

    # Check if destination exists and handle overwrite
    dest_exists = os.path.exists(dest_path)
    if dest_exists:
        result['dest_size'] = get_file_size(dest_path)
        if not overwrite and operation in ['backup', 'restore']:
            module.fail_json(msg=f"Destination file exists and overwrite=false: {dest_path}")

    try:
        if operation == 'backup':  # pylint: disable=too-many-nested-blocks
            # Verify source database before backup
            if not verify_sqlite_db(src_path):
                module.fail_json(msg=f"Source database integrity check failed: {src_path}")

            if not module.check_mode:
                backup_time = backup_database(src_path, dest_path, compress)
                result['backup_time'] = backup_time
                result['dest_size'] = get_file_size(dest_path)

                # Verify backup if requested
                if verify_backup:  # pylint: disable=too-many-nested-blocks
                    if compress:  # pylint: disable=too-many-nested-blocks
                        # For compressed backups, decompress temporarily to verify
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_path = temp_file.name
                        try:
                            with gzip.open(dest_path, 'rb') as gz_file:
                                with open(temp_path, 'wb') as temp_file:
                                    shutil.copyfileobj(gz_file, temp_file)
                            result['verified'] = verify_sqlite_db(temp_path)
                        finally:
                            os.unlink(temp_path)
                    else:
                        result['verified'] = verify_sqlite_db(dest_path)

                    if not result['verified']:
                        module.fail_json(msg="Backup verification failed")

            result['changed'] = True

        elif operation == 'restore':
            # Detect if source is compressed
            src_compressed = is_compressed_file(src_path)
            result['compressed'] = src_compressed

            if not module.check_mode:
                restore_time = restore_database(src_path, dest_path, src_compressed)
                result['backup_time'] = restore_time
                result['dest_size'] = get_file_size(dest_path)

                # Verify restored database
                if not verify_sqlite_db(dest_path):
                    module.fail_json(msg="Restored database integrity check failed")

            result['changed'] = True

        elif operation == 'verify':
            # Verify database integrity
            if src_path != '/dev/null':  # Skip verification for /dev/null
                verified = verify_sqlite_db(src_path)
                result['verified'] = verified
                if not verified:
                    module.fail_json(msg=f"Database integrity check failed: {src_path}")

    except sqlite3.Error as error:
        module.fail_json(msg=f"Operation failed: {str(error)}")

    module.exit_json(**result)


if __name__ == '__main__':
    main()
