import functools
from typing import List, Any, Tuple
from sqlalchemy import text

from sql_agent.repositories.base import BaseDatabaseRepository


class SQLiteRepository(BaseDatabaseRepository):
    @functools.lru_cache(maxsize=128)
    def get_table_schema(self, table_names: Tuple[str, ...]) -> str:
        """
        Get DDL statements for specified tables using caching for performance
        """
        ddl_statements = []

        with self.engine.connect() as conn:
            for table_name in table_names:
                result = conn.execute(text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';"))
                row = result.fetchone()
                if row and row[0]:
                    ddl_statements.append(row[0].strip() + ";")
                else:
                    ddl_statements.append(f"-- Table {table_name} not found;")

        return "\n\n".join(ddl_statements)