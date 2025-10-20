from abc import ABC, abstractmethod
from typing import List, Any, Tuple
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, IntegrityError, DataError, OperationalError

from .exceptions import ValidationError, DatabaseError


class BaseDatabaseRepository(ABC):
    def __init__(self, engine: Engine):
        self.engine = engine

    @classmethod
    def from_connection_url(cls, connection_url: str):
        """
        Factory method to create repository from connection URL
        """
        engine = create_engine(connection_url)
        return cls(engine=engine)

    def execute_query(self, query: str, max_rows: int = 1000) -> Tuple[List[str], List[List[Any]]]:
        """
        Execute a query and return results
        """
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchmany(max_rows)
                return list(columns), [list(row) for row in rows]
        except (ProgrammingError, IntegrityError, DataError, OperationalError) as e:
            raise ValidationError(str(e))
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def validate_query(self, query: str):
        """
        Validate a query for safety, raising an exception if validation fails
        """
        if not query:
            raise ValidationError("Empty SQL query")

        sql_upper = query.upper()
        if 'SELECT' not in sql_upper or 'FROM' not in sql_upper:
            raise ValidationError("Generated query does not contain SELECT and FROM clauses")

        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValidationError(f"Generated query contains potentially dangerous keyword: {keyword}")

    @abstractmethod
    def get_table_schema(self, table_names: Tuple[str, ...]) -> str:
        """
        Get DDL statements for specified tables
        
        Args:
            table_names: Tuple of table names to get schema for
            
        Returns:
            String containing DDL statements
        """
        pass