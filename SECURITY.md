# Security Best Practices

When using this collection:

1. **Database File Permissions**: Always set restrictive permissions (0640 or stricter) on SQLite database files
2. **Parameterized Queries**: Use the collection's parameterized query support to prevent SQL injection
3. **File Path Validation**: Validate database file paths to prevent directory traversal attacks
4. **Backup Security**: Secure backup files with appropriate permissions and consider encryption for sensitive data
5. **Network Access**: SQLite databases should not be directly exposed to network access

## Secure Configuration Examples

```yaml
# Secure database creation
- name: Create secure database
  samccann.sqlite.sqlite_db:
    path: /var/lib/app/secure.db
    state: present
    mode: '0640'
    owner: appuser
    group: appgroup

# Secure parameterized queries
- name: Safe data insertion
  samccann.sqlite.sqlite_query:
    db: /var/lib/app/secure.db
    query: "INSERT INTO users (name, email) VALUES (?, ?)"
    parameters:
      - "{{ user_name }}"
      - "{{ user_email }}"
```