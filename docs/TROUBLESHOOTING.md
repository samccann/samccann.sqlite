# Troubleshooting Guide

This guide covers common issues and solutions when using the SQLite Ansible Collection.

## Common Issues

### Database Locked Errors

**Problem**: `database is locked` error when trying to access SQLite database

**Causes**:

- Another process has an open connection to the database
- Previous operation didn't close connection properly
- Database file permissions issues
- WAL mode files (.db-wal, .db-shm) exist from crashed processes

**Solutions**:

1. **Check for other processes**:

   ```bash
   lsof /path/to/database.db
   fuser /path/to/database.db
   ```

2. **Clean up WAL files**:

   ```bash
   # Stop all processes using the database first
   rm /path/to/database.db-wal
   rm /path/to/database.db-shm
   ```

3. **Use timeout in queries**:

   ```yaml
   - name: Query with timeout
     samccann.sqlite.sqlite_query:
       db: /path/to/database.db
       query: "SELECT * FROM table"
       timeout: 30 # Wait up to 30 seconds
   ```

4. **Check file permissions**:
   ```bash
   ls -la /path/to/database.db
   # Ensure ansible user has read/write access
   ```

### Permission Denied Errors

**Problem**: Permission denied when creating or accessing database files

**Solutions**:

1. **Set proper ownership**:

   ```yaml
   - name: Create database with proper ownership
     samccann.sqlite.sqlite_db:
       path: /var/lib/app/database.db
       state: present
       mode: "0640"
       owner: appuser
       group: appgroup
   ```

2. **Check directory permissions**:

   ```bash
   # Ensure parent directory is writable
   chmod 755 /var/lib/app/
   ```

3. **Use SELinux context** (if applicable):
   ```bash
   setsebool -P httpd_can_network_connect_db 1
   ```

### Query Timeout Issues

**Problem**: Queries hang or timeout

**Solutions**:

1. **Increase timeout**:

   ```yaml
   - name: Long running query
     samccann.sqlite.sqlite_query:
       db: /path/to/database.db
       query: "SELECT * FROM large_table"
       timeout: 300 # 5 minutes
   ```

2. **Optimize database performance**:

   ```yaml
   - name: Optimize database
     samccann.sqlite.sqlite_db:
       path: /path/to/database.db
       state: present
       performance:
         journal_mode: WAL
         synchronous: 1
         cache_size: -16384
       maintenance:
         vacuum: true
         analyze: true
   ```

3. **Break large operations into chunks**:
   ```yaml
   - name: Process in batches
     samccann.sqlite.sqlite_query:
       db: /path/to/database.db
       query: "DELETE FROM table WHERE id BETWEEN ? AND ?"
       parameters:
         - "{{ item * 1000 }}"
         - "{{ (item + 1) * 1000 - 1 }}"
     loop: "{{ range(0, 10) | list }}"
   ```

### Backup and Restore Issues

**Problem**: Backup verification fails or corrupted backups

**Solutions**:

1. **Verify source database first**:

   ```yaml
   - name: Check database integrity before backup
     samccann.sqlite.sqlite_db:
       path: /path/to/database.db
       state: present
       maintenance:
         integrity_check: true
   ```

2. **Use incremental backups for large databases**:

   ```yaml
   - name: Create incremental backup
     samccann.sqlite.sqlite_backup:
       src: /path/to/database.db
       dest: /backup/database_{{ ansible_date_time.epoch }}.db
       operation: backup
       incremental: true
       verify_backup: true
   ```

3. **Check disk space**:
   ```bash
   df -h /backup/
   ```

### Foreign Key Constraint Failures

**Problem**: Foreign key constraint violations

**Solutions**:

1. **Ensure foreign keys are enabled**:

   ```yaml
   - name: Create database with foreign keys
     samccann.sqlite.sqlite_db:
       path: /path/to/database.db
       state: present
       foreign_keys: true
   ```

2. **Check constraint definitions**:

   ```yaml
   - name: Get table info
     samccann.sqlite.sqlite_table:
       db: /path/to/database.db
       name: child_table
       state: present
       gather_info: true
     register: table_info
   ```

3. **Disable foreign keys temporarily**:
   ```yaml
   - name: Disable foreign keys for data migration
     samccann.sqlite.sqlite_query:
       db: /path/to/database.db
       query: "PRAGMA foreign_keys = OFF"
   ```

### Performance Issues

**Problem**: Slow query performance or high disk usage

**Solutions**:

1. **Optimize database settings**:

   ```yaml
   - name: Optimize for performance
     samccann.sqlite.sqlite_db:
       path: /path/to/database.db
       state: present
       performance:
         journal_mode: WAL # Write-Ahead Logging
         synchronous: 1 # Normal synchronization
         cache_size: -32768 # 32MB cache
         temp_store: 2 # Use memory for temp files
   ```

2. **Regular maintenance**:

   ```yaml
   - name: Regular database maintenance
     samccann.sqlite.sqlite_db:
       path: /path/to/database.db
       state: present
       maintenance:
         vacuum: true # Reclaim space
         analyze: true # Update statistics
   ```

3. **Monitor database size**:

   ```yaml
   - name: Check database size
     ansible.builtin.stat:
       path: /path/to/database.db
     register: db_stat

   - name: Alert if database too large
     ansible.builtin.fail:
       msg: "Database size {{ db_stat.stat.size }} exceeds limit"
     when: db_stat.stat.size > 1073741824 # 1GB
   ```

## Debugging Tips

### Enable Debug Output

Add this to your playbook for detailed output:

```yaml
- name: Debug SQLite operations
  samccann.sqlite.sqlite_query:
    db: /path/to/database.db
    query: "SELECT name FROM sqlite_master WHERE type='table'"
    fetch: all
  register: debug_result

- name: Show debug info
  ansible.builtin.debug:
    var: debug_result
```

### Check SQLite Version

```yaml
- name: Check SQLite version
  samccann.sqlite.sqlite_query:
    db: /path/to/database.db
    query: "SELECT sqlite_version()"
    fetch: one
  register: sqlite_version

- name: Display version
  ansible.builtin.debug:
    msg: "SQLite version: {{ sqlite_version.rows[0][0] }}"
```

### Analyze Database Schema

```yaml
- name: Get all tables
  samccann.sqlite.sqlite_query:
    db: /path/to/database.db
    query: "SELECT name FROM sqlite_master WHERE type='table'"
    fetch: all
  register: tables

- name: Get table schemas
  samccann.sqlite.sqlite_table:
    db: /path/to/database.db
    name: "{{ item[0] }}"
    state: present
    gather_info: true
  register: table_schemas
  loop: "{{ tables.rows }}"
```

## Best Practices for Troubleshooting

1. **Always check database integrity** before major operations
2. **Use timeouts** for all queries to prevent hanging
3. **Monitor disk space** before backups
4. **Test with small datasets** first
5. **Keep backups** before making schema changes
6. **Use WAL mode** for better concurrency
7. **Regular maintenance** prevents many issues

## Getting Help

If you continue to experience issues:

1. Check the [GitHub Issues](https://github.com/samccann/ansible_collections_samccann_sqlite/issues)
2. Enable verbose output with `-vvv` when running ansible-playbook
3. Check system logs for additional error details
4. Provide minimal reproduction examples when reporting bugs

## Common Error Messages

| Error Message              | Likely Cause                | Solution                                |
| -------------------------- | --------------------------- | --------------------------------------- |
| `database is locked`       | Concurrent access           | Use timeouts, check for other processes |
| `no such table`            | Table doesn't exist         | Create table first or check spelling    |
| `UNIQUE constraint failed` | Duplicate key insertion     | Use `INSERT OR IGNORE` or check data    |
| `Permission denied`        | File permissions            | Fix ownership/permissions               |
| `Query timed out`          | Long-running operation      | Increase timeout or optimize query      |
| `Invalid SQL identifier`   | Special characters in names | Use valid SQL identifiers only          |
