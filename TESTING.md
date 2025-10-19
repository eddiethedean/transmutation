# Testing Guide for Transmutation

## Overview

Transmutation uses pytest for testing with support for both SQLite and PostgreSQL databases.

## Running Tests

### SQLite Tests (No setup required)

```bash
# Run only SQLite tests (no external dependencies)
pytest -k "sqlite"

# Run all tests (PostgreSQL tests will be skipped without setup)
pytest
```

### PostgreSQL Tests (Automatic with pytest-postgresql)

#### Option 1: Using pytest-postgresql (Recommended)

Install the test dependencies:

```bash
pip install -e ".[dev]"
```

**That's it!** The `pytest-postgresql` package will:
- ✅ Automatically start a temporary PostgreSQL server
- ✅ Create a test database
- ✅ Run all PostgreSQL tests
- ✅ Tear everything down after tests complete

**Requirements:**
- PostgreSQL must be installed on your system
- On macOS: `brew install postgresql`
- On Ubuntu: `sudo apt-get install postgresql`
- On Windows: Download from https://www.postgresql.org/download/

**Run PostgreSQL tests:**

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests (including PostgreSQL)
pytest

# Run only PostgreSQL tests
pytest -k "postgres"
```

#### Option 2: Using testcontainers (Docker-based)

If you prefer Docker-based testing:

```bash
# Install testcontainers
pip install testcontainers[postgresql]

# Docker must be running
# Tests will automatically use containerized PostgreSQL
pytest
```

#### Option 3: Manual PostgreSQL Setup

If you have your own PostgreSQL server:

1. Create a test database
2. Update `tests/setup_test.py`:

```python
postgres_url = 'postgresql://user:password@localhost/testdb'
```

3. Run tests:

```bash
pytest
```

## Test Structure

### Test Files

- `tests/test_alter.py` - Column and table alteration tests
- `tests/test_column.py` - Column operation tests (planned)
- `tests/test_table.py` - Table operation tests
- `tests/test_index.py` - Index operation tests
- `tests/test_constraint.py` - Constraint operation tests
- `tests/test_migration.py` - Migration system tests

### Test Fixtures

- `sqlite_setup()` - Sets up SQLite test database
- `postgres_setup()` - Sets up PostgreSQL test database
- `postgres_url_from_fixture` - Provides PostgreSQL URL from pytest-postgresql

## Coverage Reports

```bash
# Run tests with coverage
pytest --cov=transmutation --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

## Continuous Integration

For CI/CD environments, add to your workflow:

```yaml
- name: Install dependencies
  run: |
    pip install -e ".[dev]"
    
- name: Run tests
  run: |
    pytest --cov=transmutation --cov-report=xml
```

pytest-postgresql works great in CI environments without additional setup!

## Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_migration.py::TestMigrationBasic::test_add_column_upgrade_downgrade

# Run with output capture disabled (see print statements)
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

## Writing New Tests

### Basic Test Structure

```python
import unittest
from setup_test import sqlite_setup, postgres_setup

class TestMyFeature(unittest.TestCase):
    def test_my_feature_sqlite(self):
        engine, tbl1, tbl2 = sqlite_setup()
        # Your test code here
        
    def test_my_feature_postgres(self):
        engine, tbl1, tbl2 = postgres_setup()
        # Your test code here
```

### Using pytest-postgresql Fixture

```python
def test_with_postgres_fixture(postgresql):
    """Test using pytest-postgresql fixture directly."""
    from sqlalchemy import create_engine
    
    # Get connection URL
    url = f"postgresql://{postgresql.info.user}@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    
    engine = create_engine(url)
    # Your test code here
```

## Troubleshooting

### PostgreSQL Tests Skipped

If you see:
```
PostgreSQL URL not provided - install pytest-postgresql or set postgres_url
```

**Solution:**
```bash
pip install pytest-postgresql
```

### PostgreSQL Binary Not Found

If you see:
```
Could not find PostgreSQL binaries
```

**Solution:**
- Install PostgreSQL on your system
- Set the `POSTGRESQL_BIN` environment variable to point to your pg_ctl binary

### Permission Denied

If you see permission errors when pytest-postgresql tries to start:

**Solution:**
```bash
# macOS/Linux: Ensure postgres user has proper permissions
sudo chown -R $USER /usr/local/var/postgres

# Or use testcontainers instead (requires Docker)
pip install testcontainers[postgresql]
```

## Performance Tips

### Speed Up Tests

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Skip slow tests during development
pytest -m "not slow"
```

### Configure pytest-postgresql for Speed

In `tests/conftest.py`:

```python
from pytest_postgresql import factories

# Disable fsync for faster tests (safe for testing)
postgresql_proc = factories.postgresql_proc(
    postgres_options='-c fsync=off -c synchronous_commit=off -c full_page_writes=off'
)

postgresql = factories.postgresql('postgresql_proc')
```

## Summary

- ✅ **SQLite tests**: Work immediately, no setup required
- ✅ **PostgreSQL tests**: Automatic with `pip install pytest-postgresql`
- ✅ **68% code coverage** (and growing)
- ✅ **23+ passing tests** demonstrating core functionality

Happy testing! 🧪

