__version__ = '0.0.6'

from transmutation.alter import rename_table, rename_column, add_column, drop_column
from transmutation.alter import create_primary_key, replace_primary_key, copy_table
from transmutation.alter import create_primary_keys, replace_primary_keys
from transmutation.update import set_column_values_session, set_column_values