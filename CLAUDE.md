# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Ansible Collection (`samccann.sqlite`) that provides comprehensive modules and roles for managing SQLite databases. The collection includes four main modules for database operations and one demonstration role.

## Core Modules

The collection provides these modules in `plugins/modules/`:

- **sqlite_db.py**: Database file management (create/delete with permissions)
- **sqlite_table.py**: Table operations (create/drop/inspect with schema support)
- **sqlite_query.py**: SQL execution (parameterized queries with result fetching)
- **sqlite_backup.py**: Backup operations (backup/restore/verify with compression)

Each module follows Ansible standards with comprehensive documentation, examples, and return values.

## Architecture

### Module Structure
- All modules use the standard Ansible module pattern with `AnsibleModule`
- Each includes DOCUMENTATION, EXAMPLES, and RETURN sections
- Error handling with proper sqlite3 exception management
- Support for check mode where applicable (not sqlite_query due to SQL execution nature)

### Key Patterns
- **Security**: Parameterized queries to prevent SQL injection
- **Integrity**: Database verification before/after operations
- **Flexibility**: Support for compression, permissions, and ownership
- **Robustness**: Proper connection management and transaction handling

## Development Commands

### Testing
```bash
# Run all tests via tox
tox

# Individual test environments
tox -e lint                    # Pre-commit hooks (prettier, black, flake8, isort)
tox -e ansible-lint           # Ansible-specific linting
tox -e ansible-test-sanity    # Ansible sanity tests with Docker
tox -e ansible-test-units     # Unit tests with Docker
tox -e ansible-test-integration # Integration tests with Docker
```

### Code Quality
```bash
# Run pre-commit hooks
pre-commit run --all-files

# Format Python code
black plugins/

# Sort imports
isort plugins/

# Check code style
flake8 plugins/
```

### Testing Individual Modules
```bash
# Test specific integration targets
ansible-test integration sqlite_db --docker
ansible-test integration sqlite_table --docker
ansible-test integration sqlite_query --docker
ansible-test integration sqlite_backup --docker
```

### Local Development
```bash
# Install collection locally for testing
ansible-galaxy collection install .

# Run example playbooks
ansible-playbook examples/basic_setup.yml
ansible-playbook examples/maintenance.yml
```

## Testing Architecture

- **Unit tests**: Located in `tests/unit/` for individual module testing
- **Integration tests**: Located in `tests/integration/targets/` with one target per module
- **Example playbooks**: Located in `examples/` demonstrating real-world usage
- **Molecule tests**: Located in `extensions/molecule/` for role testing

## Important Files

- **galaxy.yml**: Collection metadata and dependencies
- **tox.ini**: Test automation configuration
- **pyproject.toml**: Python project configuration (black, pytest)
- **.pre-commit-config.yaml**: Code quality hooks
- **requirements.txt**: Empty (no Python dependencies)
- **test-requirements.txt**: Testing dependencies (pytest-ansible, molecule)

## Collection Dependencies

- `ansible.utils`: Core Ansible utilities
- `community.general`: Additional utility modules
- No external Python packages required (uses built-in sqlite3)

## CI/CD

The project uses GitHub Actions with workflows in `.github/workflows/`:
- **tests.yml**: Comprehensive testing pipeline (sanity, unit, integration, lint)
- **release.yml**: Release automation

Tests run on multiple Python versions (3.11, 3.12, 3.13) and skip older versions per `tox-ansible.ini`.

## Role Structure

The `roles/run/` role demonstrates the collection's capabilities:
- Creates database and tables
- Inserts sample data
- Provides table information
- Creates backups with verification
- Uses all four modules in a cohesive workflow

## Important Notes
* Your internal knowledgebase of libraries might not be up to date. When working with any external library, unless you are 100% sure that the library has a super stable interface, you will look up the latest syntax and usage via context7
* Do not say things like: "x library isn't working so I will skip it". Generally, it isn't working because you are using the incorrect syntax or patterns. This applies doubly when the user has explicitly asked you to use a specific library, if the user wanted to use another library they wouldn't have asked you to use a specific one in the first place.
* Always run linting after making major changes. Otherwise, you won't know if you've corrupted a file or made syntax errors, or are using the wrong methods, or using methods in the wrong way.
* Please organised code into separate files wherever appropriate, and follow general coding best practices about variable naming, modularity, function complexity, file sizes, commenting, etc.
* Code is read more often than it is written, make sure your code is always optimized for readability
* Unless explicitly asked otherwise, the user never wants you to do a "dummy" implementation of any given task. Never do an implementation where you tell the user: "This is how it *would* look like". Just implement the thing.
* Whenever you are starting a new task, it is of utmost importance that you have clarity about the task. You should ask the user follow up questions if you do not, rather than making incorrect assumptions.
* Do not carry out large refactors unless explicitly instructed to do so.
* When starting on a new task, you should first understand the current architecture, identify the files you will need to modify, and come up with a Plan. In the Plan, you will think through architectural aspects related to the changes you will be making, consider edge cases, and identify the best approach for the given task. Get your Plan approved by the user before writing a single line of code.
* If you are running into repeated issues with a given task, figure out the root cause instead of throwing random things at the wall and seeing what sticks, or throwing in the towel by saying "I'll just use another library / do a dummy implementation".
* You are an incredibly talented and experienced polyglot with decades of experience in diverse areas such as software architecture, system design, development, UI & UX, copywriting, and more.
* When doing UI & UX work, make sure your designs are both aesthetically pleasing, easy to use, and follow UI / UX best practices. You pay attention to interaction patterns, micro-interactions, and are proactive about creating smooth, engaging user interfaces that delight users.
* When you receive a task that is very large in scope or too vague, you will first try to break it down into smaller subtasks. If that feels difficult or still leaves you with too many open questions, push back to the user and ask them to consider breaking down the task for you, or guide them through that process. This is important because the larger the task, the more likely it is that things go wrong, wasting time and energy for everyone involved.