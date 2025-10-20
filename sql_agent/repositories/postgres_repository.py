import functools
from typing import List, Any, Tuple
from sqlalchemy import MetaData, text
from sqlalchemy.sql.ddl import CreateTable

from sql_agent.repositories.base import BaseDatabaseRepository


class PostgreSQLRepository(BaseDatabaseRepository):
    @functools.lru_cache(maxsize=128)
    def get_table_schema(self, table_names: Tuple[str, ...]) -> str:
        """
        Get DDL statements for specified tables using caching for performance
        """
        metadata = MetaData()
        ddl_statements = []

        # Reflect each table individually
        for table_name in table_names:
            metadata.reflect(bind=self.engine, only=[table_name])
            table = metadata.tables[table_name]
            ddl = str(CreateTable(table).compile(self.engine))
            ddl_statements.append(ddl.strip() + ";")

        return "\n\n".join(ddl_statements)