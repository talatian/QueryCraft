def get_repository_for_url(connection_url: str):
    """Factory function to get the appropriate repository based on the connection URL."""
    if connection_url.startswith("postgresql"):
        from sql_agent.repositories.postgres_repository import PostgreSQLRepository
        return PostgreSQLRepository.from_connection_url(connection_url)
    elif connection_url.startswith("sqlite"):
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        return SQLiteRepository.from_connection_url(connection_url)
    else:
        # Default to a more generic repository or raise an exception
        from sql_agent.repositories.postgres_repository import PostgreSQLRepository
        return PostgreSQLRepository.from_connection_url(connection_url)