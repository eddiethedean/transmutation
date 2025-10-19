"""Pytest configuration and fixtures for transmutation tests."""

import pytest


# pytest-postgresql will automatically provide a postgresql fixture
# that starts a temporary PostgreSQL server for tests

@pytest.fixture
def postgres_url_from_fixture(postgresql):
    """
    Fixture that provides a PostgreSQL connection URL from pytest-postgresql.
    
    The postgresql fixture automatically:
    - Starts a temporary PostgreSQL server
    - Creates a test database
    - Tears everything down after tests complete
    
    Args:
        postgresql: The postgresql fixture from pytest-postgresql
        
    Returns:
        str: PostgreSQL connection URL
        
    Example:
        >>> def test_something(postgres_url_from_fixture):
        ...     # Use the URL for testing
        ...     engine = create_engine(postgres_url_from_fixture)
    """
    # Get the connection info from the postgresql fixture
    host = postgresql.info.host
    port = postgresql.info.port
    user = postgresql.info.user
    dbname = postgresql.info.dbname
    
    return f"postgresql://{user}@{host}:{port}/{dbname}"


# Alternative: You can also configure custom PostgreSQL settings
# Uncomment and modify as needed:

# from pytest_postgresql import factories

# # Custom PostgreSQL process that loads specific extensions or config
# postgresql_proc = factories.postgresql_proc(
#     port=None,  # Use random port
#     postgres_options='-c shared_buffers=128MB -c fsync=off',  # Performance tweaks for tests
# )

# # Custom PostgreSQL fixture using the custom process
# postgresql = factories.postgresql('postgresql_proc')

