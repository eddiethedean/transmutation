"""Pytest configuration and fixtures for transmutation tests."""

import pytest
from typing import Optional
import setup_test

# Try to import pytest-postgresql, but don't fail if not installed
try:
    from pytest_postgresql import factories
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


if POSTGRESQL_AVAILABLE:
    # Configure PostgreSQL process with optimizations for faster tests
    postgresql_proc = factories.postgresql_proc(
        port=None,  # Use random port to avoid conflicts
        postgres_options='-c fsync=off -c synchronous_commit=off -c full_page_writes=off',
    )
    
    # Create PostgreSQL database fixture
    postgresql = factories.postgresql('postgresql_proc')


@pytest.fixture(scope="session", autouse=True)
def setup_postgresql_url(request):
    """
    Session-scoped fixture that sets up PostgreSQL URL for all tests.
    
    This uses autouse=True so it runs automatically for all tests.
    If pytest-postgresql is available, it will provide a working URL.
    """
    if POSTGRESQL_AVAILABLE:
        # We need to get the postgresql fixture in a session scope way
        # This is a workaround since we can't directly use the postgresql fixture here
        pass
    # If not available, tests will skip as needed


@pytest.fixture(scope="function", autouse=True)
def postgres_url(request):
    """
    Fixture that provides a PostgreSQL connection URL from pytest-postgresql.
    
    This fixture has autouse=True so it runs automatically for all tests.
    It only sets up PostgreSQL if the test name contains 'postgres' or 'schema'.
    
    The postgresql fixture automatically:
    - Starts a temporary PostgreSQL server
    - Creates a test database
    - Tears everything down after tests complete
    
    Args:
        request: pytest request object
        
    Returns:
        str or None: PostgreSQL connection URL, or None if not needed
    """
    # Only setup PostgreSQL for tests that need it
    test_name = request.node.name.lower()
    needs_postgres = 'postgres' in test_name or 'schema' in test_name
    
    if not needs_postgres:
        return None
    
    if not POSTGRESQL_AVAILABLE:
        pytest.skip("pytest-postgresql not installed")
    
    # Request the postgresql fixture
    postgresql = request.getfixturevalue('postgresql')
    
    # Get the connection info from the postgresql fixture
    host = postgresql.info.host
    port = postgresql.info.port
    user = postgresql.info.user
    dbname = postgresql.info.dbname
    
    url = f"postgresql://{user}@{host}:{port}/{dbname}"
    
    # Set the URL in setup_test module so existing tests can use it
    setup_test.set_postgres_url(url)
    
    return url


# Create a fixture that provides postgres_setup function with URL pre-configured
@pytest.fixture
def postgres_setup_func(postgres_url):
    """
    Fixture that provides a postgres_setup function with URL already configured.
    
    Returns:
        callable: postgres_setup function that uses the temporary PostgreSQL database
    """
    def _postgres_setup(schema=None):
        return setup_test.postgres_setup(postgres_url=postgres_url, schema=schema)
    
    return _postgres_setup

