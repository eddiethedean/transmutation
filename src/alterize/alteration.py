from dataclasses import dataclass
from typing import Optional, Protocol

from sqlalchemy.engine import Engine
from sqlalchemize.features import get_column_types, get_table

from alterize.alter import rename_column, drop_column, add_column


class Alteration(Protocol):
    def upgrade(self) -> None:
        ...

    def downgrade(self) -> None:
        ...


@dataclass
class RenameColumn(Alteration):
    table_name: str
    old_col_name: str
    new_col_name: str
    engine: Engine
    schema: Optional[str] = None

    def upgrade(self) -> None:
        rename_column(
            self.table_name,
            self.old_col_name,
            self.new_col_name,
            self.engine,
            self.schema
        )

    def downgrade(self) -> None:
        rename_column(
            self.table_name,
            self.new_col_name,
            self.old_col_name,
            self.engine,
            self.schema
        )


@dataclass
class DropColumn(Alteration):
    table_name: str
    col_name: str
    engine: Engine
    schema: Optional[str] = None

    def upgrade(self) -> None:
        table = get_table(self.table_name, self.engine, self.schema)
        self.dtype = get_column_types(table)[self.table_name]
        drop_column(
            self.table_name,
            self.col_name,
            self.engine,
            self.schema
        )

    def downgrade(self) -> None:
        add_column(
            self.table_name,
            self.col_name,
            self.dtype,
            self.engine,
            self.schema
        )
        