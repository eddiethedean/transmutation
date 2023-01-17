from typing import Optional, Protocol

from sqlalchemy.engine import Engine
from alembic.operations import Operations

from alterize.alter import _get_op
from alterize.alteration import DropColumn, RenameColumn


class Alteration(Protocol):
    def upgrade(self) -> None:
        ...

    def downgrade(self) -> None:
        ...


class Migration:
    """Keep track of alterations and allow rollback of changes."""
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.upgrades: list[Alteration] = []
        self.downgrades: list[Alteration] = []

    @property
    def _op(self) -> Operations:
        return _get_op(self.engine)

    def add_upgrade(self, alteration: Alteration) -> None:
        self.upgrades.append(alteration)

    def add_downgrade(self, alteration: Alteration) -> None:
        self.downgrades.append(alteration)

    def upgrade(self) -> None:
        for i, alteration in enumerate(list(self.upgrades)):
            alteration.upgrade()
            self.add_downgrade(alteration)
            del self.upgrades[i]

    def downgrade(self) -> None:
        for i, alteration in enumerate(list(self.downgrades)):
            alteration.downgrade()
            del self.downgrades[i]

    def rename_column(
        self,
        table_name: str,
        old_col_name: str,
        new_col_name: str,
        engine: Engine,
        schema: Optional[str] = None
    ) -> None:
        alteration = RenameColumn(
            table_name,
            old_col_name,
            new_col_name,
            engine,
            schema
        )
        self.add_upgrade(alteration)

    def drop_column(
        self,
        table_name: str,
        col_name: str,
        engine: Engine,
        schema: Optional[str] = None
    ) -> None:
        alteration = DropColumn(
            table_name,
            col_name,
            engine,
            schema
        )
        self.add_upgrade(alteration)
    