# Cursor SQLite Collection

This repository contains the `samccann.sqlite` Ansible Collection for managing SQLite databases.

## Description

The Cursor SQLite Collection provides comprehensive modules and roles for managing SQLite databases, including:

- **Database Management**: Create, delete, and configure SQLite databases
- **Table Operations**: Create, drop, and inspect database tables
- **Query Execution**: Run SQL queries with support for parameterized queries
- **Backup & Restore**: Create and restore database backups with optional compression
- **Integrity Checks**: Verify database integrity and backup validation

## Requirements

- Ansible >= 2.9
- Python >= 3.6
- sqlite3 (built-in Python module)

## Installation

```bash
ansible-galaxy collection install samccann.sqlite
```

You can also include it in a `requirements.yml` file:

```yaml
collections:
  - name: samccann.sqlite
```

## Modules

### samccann.sqlite.sqlite_db

Manage SQLite database files.

```yaml
- name: Create SQLite database
  samccann.sqlite.sqlite_db:
    path: /var/lib/app/myapp.db
    state: present
    mode: '0640'
    owner: appuser
    group: appgroup
```

### samccann.sqlite.sqlite_table

Manage database tables.

```yaml
- name: Create users table
  samccann.sqlite.sqlite_table:
    db: /var/lib/app/myapp.db
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
```

### samccann.sqlite.sqlite_query

Execute SQL queries.

```yaml
- name: Insert user data
  samccann.sqlite.sqlite_query:
    db: /var/lib/app/myapp.db
    query: "INSERT INTO users (username, email) VALUES (?, ?)"
    parameters:
      - "john_doe"
      - "john@example.com"

- name: Select all users
  samccann.sqlite.sqlite_query:
    db: /var/lib/app/myapp.db
    query: "SELECT * FROM users"
    fetch: all
  register: all_users
```

### samccann.sqlite.sqlite_backup

Backup and restore databases.

```yaml
- name: Create compressed backup
  samccann.sqlite.sqlite_backup:
    src: /var/lib/app/myapp.db
    dest: /backup/myapp_backup.db.gz
    operation: backup
    compress: true
    verify_backup: true

- name: Restore from backup
  samccann.sqlite.sqlite_backup:
    src: /backup/myapp_backup.db.gz
    dest: /var/lib/app/restored.db
    operation: restore
    overwrite: true
```

## Roles

### samccann.sqlite.run

A complete role that demonstrates SQLite database management operations.

**Variables:**

- `run_sqlite_db_path`: Path to the SQLite database (default: `/tmp/example.db`)
- `run_sqlite_db_permissions`: Database file permissions (default: `'0640'`)
- `run_sqlite_backup_path`: Backup file path (default: `/tmp/example_backup.db`)
- `run_create_backup`: Whether to create backups (default: `false`)
- `run_sample_users`: List of sample users to insert
- `run_verify_integrity`: Verify database integrity (default: `true`)

**Example Usage:**

```yaml
- name: Run SQLite database setup
  include_role:
    name: samccann.sqlite.run
  vars:
    run_sqlite_db_path: /var/lib/myapp/database.db
    run_create_backup: true
    run_sample_users:
      - username: admin
        email: admin@myapp.com
      - username: user1
        email: user1@myapp.com
```

## Example Playbooks

### Basic Database Setup

```yaml
---
- name: SQLite Database Setup
  hosts: localhost
  tasks:
    - name: Create application database
      samccann.sqlite.sqlite_db:
        path: /var/lib/myapp/app.db
        state: present
        mode: '0640'

    - name: Create application tables
      samccann.sqlite.sqlite_table:
        db: /var/lib/myapp/app.db
        name: "{{ item.name }}"
        state: present
        columns: "{{ item.columns }}"
      loop:
        - name: users
          columns:
            - name: id
              type: INTEGER
              constraints: PRIMARY KEY AUTOINCREMENT
            - name: username
              type: TEXT
              constraints: NOT NULL UNIQUE
            - name: created_at
              type: TIMESTAMP
              constraints: DEFAULT CURRENT_TIMESTAMP
        - name: sessions
          columns:
            - name: id
              type: TEXT
              constraints: PRIMARY KEY
            - name: user_id
              type: INTEGER
              constraints: NOT NULL
            - name: expires_at
              type: TIMESTAMP
```

### Database Maintenance

```yaml
---
- name: SQLite Database Maintenance
  hosts: localhost
  tasks:
    - name: Create daily backup
      samccann.sqlite.sqlite_backup:
        src: /var/lib/myapp/app.db
        dest: "/backup/app_{{ ansible_date_time.date }}.db.gz"
        operation: backup
        compress: true
        verify_backup: true

    - name: Check database integrity
      samccann.sqlite.sqlite_backup:
        src: /var/lib/myapp/app.db
        dest: /dev/null
        operation: verify

    - name: Get database statistics
      samccann.sqlite.sqlite_query:
        db: /var/lib/myapp/app.db
        query: |
          SELECT
            name as table_name,
            (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as exists,
            (SELECT COUNT(*) FROM pragma_table_info(m.name)) as column_count
          FROM sqlite_master m
          WHERE type='table' AND name NOT LIKE 'sqlite_%'
        fetch: all
      register: db_stats

    - name: Display statistics
      debug:
        var: db_stats.rows
```

## Best Practices

1. **Security**: Always set appropriate file permissions on database files
2. **Backups**: Regularly backup your databases with integrity verification
3. **Parameterized Queries**: Use parameterized queries to prevent SQL injection
4. **Transactions**: Use transactions for multi-statement operations
5. **Error Handling**: Always handle database errors gracefully

## Contributing

Please read [CONTRIBUTING](CONTRIBUTING) for details on our code of conduct and the process for submitting pull requests.

This collection was initially drafted  by assisted AI via Cursor and the claude-4-sonnet model.

## License

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
