from typing import Optional, Tuple
import threading
import tempfile

import sqlalchemy as sa
import sqlalchemy.schema as sa_schema
import sqlalchemy.ext.declarative as sa_declarative
import sqlalchemy.engine as sa_engine
import sqlalchemy.orm.session as sa_session
import os

# Thread-local storage for engines that need cleanup
_thread_local = threading.local()


def _register_engine_for_cleanup(engine: sa_engine.Engine) -> None:
    """Register an engine for cleanup at process exit."""
    if not hasattr(_thread_local, "engines"):
        _thread_local.engines = []
    _thread_local.engines.append(engine)


def _cleanup_thread_engines() -> None:
    """Cleanup all engines for the current thread."""
    if hasattr(_thread_local, "engines"):
        for engine in _thread_local.engines[:]:
            try:
                engine.dispose(close=True)
                if hasattr(engine, "_testing_server"):
                    server = engine._testing_server
                    try:
                        server.stop()
                    except Exception:
                        pass
            except Exception:
                pass
        _thread_local.engines.clear()


def setup(
    connection_string: str, schema: Optional[str] = None
) -> Tuple[sa_engine.Engine, sa.Table, sa.Table]:
    Base = sa_declarative.declarative_base()

    # Configure engine for testing
    engine_kwargs = {"echo": False}

    # Only apply pool settings to non-SQLite databases
    # SQLite doesn't need special pool configuration for file-based databases
    if not connection_string.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_pre_ping": True,
                "pool_size": 2,
                "max_overflow": 0,
                "pool_recycle": 300,
            }
        )

    engine = sa.create_engine(connection_string, **engine_kwargs)

    if schema is not None:
        insp = sa.inspect(engine)
        with engine.connect() as conn:
            if schema not in insp.get_schema_names(conn):
                with conn.begin():
                    conn.execute(sa_schema.CreateSchema(schema))

    class People(Base):
        __tablename__ = "people"
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        name = sa.Column(sa.String(20))
        age = sa.Column(sa.Integer)
        address_id = sa.Column(sa.Integer)
        if schema is not None:
            __table_args__ = {"schema": schema}

    class Places(Base):
        __tablename__ = "places"
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        address = sa.Column(sa.String(100))
        city = sa.Column(sa.String(30))
        state = sa.Column(sa.String(2))
        zipcode = sa.Column(sa.Integer)

        if schema is not None:
            __table_args__ = {"schema": schema}

    Base.metadata.reflect(bind=engine, schema=schema)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine, tables=[People.__table__, Places.__table__])

    people = [
        People(name="Olivia", age=17, address_id=1),
        People(name="Liam", age=18, address_id=1),
        People(name="Emma", age=19, address_id=2),
        People(name="Noah", age=20, address_id=2),
    ]

    places = [
        Places(
            address="1600 Pennsylvania Avenue NW",
            city="San Antonio",
            state="TX",
            zipcode=78205,
        ),
        Places(address="300 Alamo Plaza", city="Washington", state="DC", zipcode=20500),
    ]

    with sa_session.Session(engine) as session, session.begin():
        session.add_all(people)
        session.add_all(places)

    return engine, People.__table__, Places.__table__


def sqlite_setup(path=None, schema=None) -> Tuple[sa_engine.Engine, sa.Table, sa.Table]:
    """
    Setup SQLite test database.

    Args:
        path: SQLite database path (defaults to unique file per worker/test)
        schema: Optional schema name (not used for SQLite)

    Returns:
        Tuple of (engine, people_table, places_table)
    """
    # Allow overriding backend via environment to reuse tests across databases
    backend = os.environ.get("TRANSMUTATION_TEST_DB", "sqlite").lower()
    if backend == "postgres":
        return postgres_setup(schema=schema)
    if backend == "mysql":
        return mysql_setup(schema=schema)

    # Use in-memory database for parallel tests to avoid file conflicts
    # or generate unique database file per worker if using files
    if path is None:
        # Check if running with pytest-xdist (parallel execution)
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
        if worker_id:
            # Use temporary file-based database per worker for parallel execution
            # This ensures all connections from the same engine share the database
            # which is needed for tests using engine.begin() or engine.connect()
            # Each worker gets its own temp file, avoiding conflicts
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".db", dir=tempfile.gettempdir()
            )
            temp_file.close()
            path = f"sqlite:///{temp_file.name}"
        else:
            # Single worker - can use file-based database
            path = "sqlite:///data/test.db"

    return setup(path, schema=schema)


def postgres_setup(
    schema: Optional[str] = None,
) -> Tuple[sa_engine.Engine, sa.Table, sa.Table]:
    """Setup ephemeral PostgreSQL using testing.postgresql, if available.

    Configured with minimal shared memory settings to support parallel execution.
    """
    try:
        import testing.postgresql  # type: ignore
    except Exception as exc:  # pragma: no cover - import-time guard
        raise RuntimeError("testing.postgresql is required for postgres tests") from exc

    Postgresql = testing.postgresql.Postgresql

    # Configure PostgreSQL with minimal shared memory for parallel test execution
    # These settings significantly reduce shared memory footprint per instance
    # Pass as postgres server command-line arguments (-c flags)
    # postgres_args must be a string, not a list
    minimal_settings = (
        "-h 127.0.0.1 -F -c logging_collector=off "  # Default settings
        "-c shared_buffers=128kB "  # Minimal shared buffers (default ~128MB)
        "-c max_connections=5 "  # Very few connections needed for tests
        "-c dynamic_shared_memory_type=none "  # Disable dynamic shared memory
        "-c max_wal_size=1MB "  # Minimal WAL size
        "-c min_wal_size=512kB "  # Minimal WAL size
        "-c maintenance_work_mem=1MB "  # Minimal maintenance memory
        "-c work_mem=1MB "  # Minimal work memory per operation
        "-c effective_cache_size=4MB "  # Minimal cache size
        "-c temp_buffers=128kB "  # Minimal temp buffers
        "-c wal_buffers=16kB "  # Minimal WAL buffers
        "-c huge_pages=off"  # Disable huge pages
    )

    pg = Postgresql(settings={"postgres_args": minimal_settings})
    dsn = pg.dsn()
    user = dsn.get("user", "postgres")
    password = dsn.get("password", "")
    host = dsn.get("host", "127.0.0.1")
    port = dsn.get("port", 5432)
    database = dsn.get("database", dsn.get("dbname", "postgres"))
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    engine, people, places = setup(url, schema=schema)
    # Attach stop handle to engine so test can keep server alive for duration
    engine._testing_server = pg  # type: ignore[attr-defined]
    _register_engine_for_cleanup(engine)
    return engine, people, places


def mysql_setup(
    schema: Optional[str] = None,
) -> Tuple[sa_engine.Engine, sa.Table, sa.Table]:
    """Setup ephemeral MySQL using testing.mysqld, if available."""
    try:
        import testing.mysqld  # type: ignore
    except Exception as exc:  # pragma: no cover - import-time guard
        raise RuntimeError("testing.mysqld is required for mysql tests") from exc

    Mysqld = testing.mysqld.Mysqld
    mysqld = Mysqld()
    dsn = mysqld.dsn()
    user = dsn.get("user", "root")
    password = dsn.get("passwd", "")
    host = dsn.get("host", "127.0.0.1")
    port = dsn.get("port", 3306)
    db = dsn.get("db", "test")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
    engine, people, places = setup(url, schema=schema)
    engine._testing_server = mysqld  # type: ignore[attr-defined]
    _register_engine_for_cleanup(engine)
    return engine, people, places
