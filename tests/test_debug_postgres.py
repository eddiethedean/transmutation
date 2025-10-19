"""Debug test to check if PostgreSQL fixture is working."""

import pytest
import setup_test


def test_postgres_url_from_fixture(postgres_url):
    """Test that postgres_url fixture provides a URL."""
    print(f"\n=== DEBUG: postgres_url from fixture: {postgres_url}")
    print(f"=== DEBUG: setup_test.postgres_url: {setup_test.postgres_url}")
    assert postgres_url is not None
    assert setup_test.postgres_url is not None
    assert setup_test.postgres_url == postgres_url


def test_postgres_setup_with_fixture():
    """Test that postgres_setup can use the fixture URL."""
    print(f"\n=== DEBUG: Before postgres_setup, URL is: {setup_test.postgres_url}")
    
    if setup_test.postgres_url is None:
        pytest.skip("No PostgreSQL URL available")
    
    engine, tbl1, tbl2 = setup_test.postgres_setup(
        postgres_url=setup_test.postgres_url
    )
    
    assert engine is not None
    print(f"=== DEBUG: Successfully created engine: {engine}")

