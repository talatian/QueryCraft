class DatabaseError(Exception):
    """Raised when the database is not functioning properly."""
    pass


class AgentFailure(Exception):
    """Raised when can not answer the question"""
    pass
