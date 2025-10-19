"""Tests for alter operations - pytest style."""

import pytest
from setup_test import sqlite_setup, postgres_setup
from fullmetalalchemy.features import get_table, get_column

from transmutation.alter import rename_column, drop_column, add_column, rename_table
from transmutation.alter import copy_table

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc


# Pytest marker to use postgres_url fixture in all tests
pytestmark = pytest.mark.usefixtures("postgres_url")


# rename_column tests
@pytest.mark.parametrize("setup_func,schema", [
    (sqlite_setup, None),
    (postgres_setup, None),
    (postgres_setup, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_rename_column(setup_func, schema):
    """Test renaming a column."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    rename_column(table.name, 'name', 'first_name', engine, schema=schema)
    table = get_table(table.name, engine, schema=schema)
    cols = set(table.columns.keys())
    assert cols == {'id', 'age', 'first_name', 'address_id'}


@pytest.mark.parametrize("setup_func,error,schema", [
    (sqlite_setup, KeyError, None),
    (postgres_setup, sa_exc.ProgrammingError, None),
    (postgres_setup, sa_exc.ProgrammingError, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_rename_column_key_error(setup_func, error, schema):
    """Test renaming a non-existent column raises error."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    with pytest.raises(error):
        rename_column(table.name, 'names', 'first_name', engine, schema=schema)


@pytest.mark.parametrize("setup_func,error,schema", [
    (sqlite_setup, sa_exc.OperationalError, None),
    (postgres_setup, sa_exc.ProgrammingError, None),
    (postgres_setup, sa_exc.ProgrammingError, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_rename_column_op_error(setup_func, error, schema):
    """Test renaming to existing column name raises error."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    with pytest.raises(error):
        rename_column(table.name, 'name', 'age', engine, schema=schema)


# drop_column tests
@pytest.mark.parametrize("setup_func,schema", [
    (sqlite_setup, None),
    (postgres_setup, None),
    (postgres_setup, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_drop_column(setup_func, schema):
    """Test dropping a column."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    drop_column(table.name, 'name', engine, schema=schema)
    table = get_table(table.name, engine, schema=schema)
    cols = set(table.columns.keys())
    assert cols == {'id', 'age', 'address_id'}


@pytest.mark.parametrize("setup_func,error,schema", [
    (sqlite_setup, KeyError, None),
    (postgres_setup, sa_exc.ProgrammingError, None),
    (postgres_setup, sa_exc.ProgrammingError, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_drop_column_key_error(setup_func, error, schema):
    """Test dropping a non-existent column raises error."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    with pytest.raises(error):
        drop_column(table.name, 'names', engine, schema=schema)


# add_column tests
@pytest.mark.parametrize("setup_func,schema", [
    (sqlite_setup, None),
    (postgres_setup, None),
    (postgres_setup, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_add_column(setup_func, schema):
    """Test adding a column."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    table = add_column(table.name, 'last_name', str, engine, schema=schema)
    cols = set(table.columns.keys())
    assert cols == {'id', 'age', 'name', 'address_id', 'last_name'}
    assert sa.VARCHAR == type(get_column(table, 'last_name').type)


@pytest.mark.parametrize("setup_func,error,schema", [
    (sqlite_setup, sa_exc.OperationalError, None),
    (postgres_setup, sa_exc.ProgrammingError, None),
    (postgres_setup, sa_exc.ProgrammingError, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_add_column_op_error(setup_func, error, schema):
    """Test adding a duplicate column name raises error."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    with pytest.raises(error):
        add_column(table.name, 'name', str, engine, schema=schema)


# rename_table tests
@pytest.mark.parametrize("setup_func,schema", [
    (sqlite_setup, None),
    (postgres_setup, None),
    (postgres_setup, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_rename_table(setup_func, schema):
    """Test renaming a table."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    new_table_name = 'employees'
    table_names = sa.inspect(engine).get_table_names(schema=schema)
    table_names.remove(table.name)
    table = rename_table(table.name, new_table_name, engine, schema=schema)
    table_names.append(new_table_name)
    new_table_names = sa.inspect(engine).get_table_names(schema=schema)
    assert set(table_names) == set(new_table_names)


@pytest.mark.parametrize("setup_func,error,schema", [
    (sqlite_setup, sa_exc.OperationalError, None),
    (postgres_setup, sa_exc.ProgrammingError, None),
    (postgres_setup, sa_exc.ProgrammingError, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_rename_table_fail(setup_func, error, schema):
    """Test renaming to existing table name raises error."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    new_table_name = 'places'
    with pytest.raises(error):
        rename_table(table.name, new_table_name, engine, schema=schema)


# copy_table tests
@pytest.mark.parametrize("setup_func,schema", [
    (sqlite_setup, None),
    (postgres_setup, None),
    (postgres_setup, 'local'),
], ids=["sqlite", "postgres", "postgres-schema"])
def test_copy_table(setup_func, schema):
    """Test copying a table."""
    engine, tbl1, tbl2 = setup_func(schema=schema)
    table = get_table('people', engine, schema=schema)
    new_table_name = 'employees'
    table_names = sa.inspect(engine).get_table_names(schema=schema)
    copy_table(table, new_table_name, engine, schema=schema)
    table_names.append(new_table_name)
    new_table_names = sa.inspect(engine).get_table_names(schema=schema)
    assert set(table_names) == set(new_table_names)

