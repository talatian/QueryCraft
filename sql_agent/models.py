from typing import List, Any, Annotated

from pydantic import BaseModel
from operator import add


class Result(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    total_rows: int


class ValidationResult(BaseModel):
    is_valid: bool
    feedback: str = None


class State(BaseModel):
    question: str
    sql_query: str = None
    validation_result: ValidationResult = None
    result: Result = None
    error: str = None
    total_generations: Annotated[int, add] = 0
