class RepositoryException(Exception):
    """Base exception for repository operations."""
    pass


class ValidationError(RepositoryException):
    """Exception raised when a query fails validation."""
    pass


class DatabaseError(RepositoryException):
    """Exception raised when a database operation fails."""
    pass
