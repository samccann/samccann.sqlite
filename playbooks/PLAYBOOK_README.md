# Family Database Playbooks

This directory contains several Ansible playbooks that demonstrate the usage of the `community.sqlite` collection to create a family database with sibling information.

## 📁 Available Playbooks

### 1. `family_database_simple.yml` (Recommended)

A comprehensive, production-ready playbook that creates a family database with 6 siblings.

**Features:**

- Creates SQLite database named `family.db`
- Creates `siblings` table with comprehensive schema
- Inserts 6 sibling records with names, ages, and favorite colors
- Creates automatic backup
- Provides detailed progress feedback
- Includes verification commands

**Usage:**

```bash
cd playbooks
ansible-playbook family_database_simple.yml
```

### 2. `create_family_db.yml`

A basic version that demonstrates the core functionality.

### 3. `test_family_local.yml`

A minimal test version for development and testing.

### 4. `family_database_complete.yml`

An advanced version with additional analytics and features.

### 5. `family_database.yml`

A hybrid version that supports both local modules and FQCN usage.

## 📊 Database Schema

The playbooks create a `siblings` table with the following structure:

```sql
CREATE TABLE siblings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    birth_order INTEGER NOT NULL,
    age INTEGER,
    favorite_color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 👥 Family Data

The database is populated with the following siblings:

| Birth Order | Name   | Age | Favorite Color |
| ----------- | ------ | --- | -------------- |
| 1           | David  | 65  | Blue           |
| 2           | Caryl  | 63  | Green          |
| 3           | Joyce  | 61  | Purple         |
| 4           | Tom    | 59  | Red            |
| 5           | Linda  | 57  | Yellow         |
| 6           | Sharon | 55  | Pink           |

## 🔧 Prerequisites

1. **Ansible**: Version 2.9 or higher
2. **Python**: Version 3.6 or higher with sqlite3 module
3. **SQLite**: Command-line tools (for verification)

## 🚀 Quick Start

1. **Navigate to the playbooks directory:**

   ```bash
   cd /path/to/ansible_collections/community/sqlite/playbooks
   ```

2. **Run the main playbook:**

   ```bash
   ansible-playbook family_database_simple.yml
   ```

3. **Verify the database was created:**
   ```bash
   sqlite3 family.db "SELECT * FROM siblings ORDER BY birth_order;"
   ```

## 📋 Output Files

After running the playbook, you'll have:

- `family.db` - The main SQLite database
- `family_backup.db` - Automatic backup of the database

## 🔍 Verification Commands

### View all siblings:

```bash
sqlite3 family.db "SELECT birth_order, name, age, favorite_color FROM siblings ORDER BY birth_order;"
```

### View table schema:

```bash
sqlite3 family.db ".schema siblings"
```

### View all tables:

```bash
sqlite3 family.db ".tables"
```

### Get database info:

```bash
sqlite3 family.db ".dbinfo"
```

## 🛠 Configuration

### Custom Database Path

You can specify a custom database location:

```bash
ansible-playbook family_database_simple.yml -e database_path="/custom/path/family.db"
```

### Custom Backup Path

You can specify a custom backup location:

```bash
ansible-playbook family_database_simple.yml -e backup_path="/backup/family_backup.db"
```

## 📊 Example Output

When you run the playbook, you'll see output like:

```
✅ Family database created at ./family.db (4096 bytes)
✅ Siblings table created
✅ Successfully inserted 6 siblings
👥 Total siblings in family database: 6

👥 FAMILY SIBLINGS DATABASE:
1. David (65 years old, loves Blue)
2. Caryl (63 years old, loves Green)
3. Joyce (61 years old, loves Purple)
4. Tom (59 years old, loves Red)
5. Linda (57 years old, loves Yellow)
6. Sharon (55 years old, loves Pink)

🎉 FAMILY DATABASE CREATED SUCCESSFULLY! 🎉
```

## 🧪 Testing

To test that everything works correctly:

1. **Navigate to playbooks directory:**

   ```bash
   cd playbooks
   ```

2. **Run the playbook:**

   ```bash
   ansible-playbook family_database_simple.yml
   ```

3. **Verify the data:**

   ```bash
   sqlite3 family.db "SELECT COUNT(*) FROM siblings;"
   # Should return: 6
   ```

4. **Check backup was created:**
   ```bash
   ls -la family_backup.db
   ```

## 🔧 Troubleshooting

### Module Not Found Errors

If you get "module not found" errors:

1. **For local development** (running from collection directory):

   ```bash
   cd /path/to/ansible_collections/community/sqlite/playbooks
   ansible-playbook family_database_simple.yml
   ```

2. **For installed collection**, use the FQCN version:
   ```bash
   ansible-playbook family_database.yml -e use_fqcn=true
   ```

### Permission Errors

Ensure you have write permissions in the directory where you're running the playbook.

### SQLite Command Not Found

Install SQLite tools:

```bash
# Ubuntu/Debian
sudo apt-get install sqlite3

# RHEL/CentOS/Fedora
sudo yum install sqlite  # or dnf install sqlite
```

## 📝 Customization

You can modify the `siblings_data` variable in any playbook to change the family members:

```yaml
siblings_data:
  - { name: "Your Name", birth_order: 1, age: 30, favorite_color: "Blue" }
  - { name: "Sibling Name", birth_order: 2, age: 28, favorite_color: "Red" }
  # Add more siblings as needed
```

## 🎯 Use Cases

These playbooks demonstrate:

- **Database Creation**: Using `sqlite_db` module
- **Table Management**: Using `sqlite_table` module
- **Data Insertion**: Using `sqlite_query` module with parameters
- **Backup Operations**: Using `sqlite_backup` module
- **Data Retrieval**: Querying and displaying results
- **Error Handling**: Proper module usage patterns

## 📚 Collection Modules Used

- `sqlite_db`: Database creation and management
- `sqlite_table`: Table creation and schema management
- `sqlite_query`: SQL query execution and data manipulation
- `sqlite_backup`: Database backup and restore operations

## 🤝 Contributing

Feel free to modify these playbooks to suit your needs or contribute improvements back to the collection!
