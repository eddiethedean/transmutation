"""Pytest configuration and fixtures for transmutation tests.

Adds opt-in markers to run tests against ephemeral PostgreSQL and MySQL
using testing.postgresql and testing.mysqld. Default backend remains SQLite.
"""

import os
from typing import List

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "postgres: run test using PostgreSQL ephemeral server"
    )
    config.addinivalue_line("markers", "mysql: run test using MySQL ephemeral server")
    config.addinivalue_line(
        "markers", "multidb: placeholder marker when orchestrating multi-db runs"
    )


def _ensure_dependency(import_path: str) -> bool:
    try:
        __import__(import_path)
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    markexpr = getattr(config.option, "markexpr", "").strip()
    if markexpr in ("postgres", "mysql"):
        mark = getattr(pytest.mark, markexpr)
        for item in items:
            item.add_marker(mark)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    # Default to sqlite unless a backend marker is present
    if item.get_closest_marker("postgres"):
        if not _ensure_dependency("testing.postgresql"):
            pytest.skip("testing.postgresql not available; skipping postgres tests")
        os.environ["TRANSMUTATION_TEST_DB"] = "postgres"
    elif item.get_closest_marker("mysql"):
        if not _ensure_dependency("testing.mysqld"):
            pytest.skip("testing.mysqld not available; skipping mysql tests")
        os.environ["TRANSMUTATION_TEST_DB"] = "mysql"
    else:
        os.environ.pop("TRANSMUTATION_TEST_DB", None)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    """Cleanup engines and servers after each test."""
    # Import here to avoid circular imports
    from setup_test import _cleanup_thread_engines

    # Cleanup all engines for this thread
    _cleanup_thread_engines()

    # Clear environment variable
    os.environ.pop("TRANSMUTATION_TEST_DB", None)
