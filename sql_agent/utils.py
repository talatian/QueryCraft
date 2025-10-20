import functools
from typing import Tuple

from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql.ddl import CreateTable

from sql_agent.models import ValidationResult


@functools.lru_cache(maxsize=128)
def extract_table_metadata_ddl(connection_url: str, table_names: Tuple[str, ...]) -> str:
    """
    Connect to a database using the given connection URL and return
    DDL statements (CREATE TABLE ...) for the given tables.

    Args:
        connection_url (str): SQLAlchemy-style database URL, e.g. "postgresql+psycopg2://user:pass@host/db"
        table_names (tuple[str]): List of table names to extract DDL from.

    Returns:
        str: Concatenated CREATE TABLE statements
    """

    engine = create_engine(connection_url)
    metadata = MetaData()

    ddl_statements = []

    with engine.connect() as conn:
        # Reflect each table individually
        for table_name in table_names:
            metadata.reflect(conn, only=[table_name])
            table = metadata.tables[table_name]

            # Generate the CREATE TABLE DDL (includes foreign keys, etc.)
            ddl = str(CreateTable(table).compile(engine))
            ddl_statements.append(ddl.strip() + ";")

        # Join all CREATE statements with a newline
        return "\n\n".join(ddl_statements)


def validate_sql_query(query) -> ValidationResult:
    """Validate the generated SQL query"""

    # Basic validation checks
    if not query:
        return ValidationResult(is_valid=False, feedback="Empty SQL query")

    # Check if query contains SELECT and FROM (basic requirement for safe queries)
    sql_upper = query.upper()
    if 'SELECT' not in sql_upper or 'FROM' not in sql_upper:
        return ValidationResult(is_valid=False, feedback="Generated query does not contain SELECT and FROM clauses")

    # Prevent potentially dangerous commands
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return ValidationResult(
                is_valid=False,
                feedback=f"Generated query contains potentially dangerous keyword: {keyword}"
            )

    return ValidationResult(is_valid=True)
