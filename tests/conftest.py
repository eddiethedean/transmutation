"""Pytest configuration and fixtures for transmutation tests.

This configuration is set up for SQLite testing only, which requires no external
database setup and is fast and reliable for CI/CD.
"""



# No special configuration needed for SQLite tests
# All tests use sqlite:///data/test.db which is created automatically
