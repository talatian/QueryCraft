import logging

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from sql_agent.exceptions import AgentFailure, DatabaseFailure
from sql_agent.models import State, Result, ValidationResult
from sql_agent.repositories.exceptions import ValidationError, DatabaseError
from sql_agent.sql_coder.generator import sql_generator, Query, Feedback, sql_corrector

logger = logging.getLogger(__name__)


def sql_generation_node(state: State, config: RunnableConfig):
    """Generate SQL query from natural language question using Ollama"""

    if state.total_generations >= config["configurable"]["max_generations"]:
        raise AgentFailure("Agent could not answer the question")

    # Get repository from config
    repository = config["configurable"]["repository"]
    db_table_names = config["configurable"]["db_table_names"]

    # Get the current database schema using repository
    database_schema = repository.get_table_schema(db_table_names)

    if state.validation_result:
        sql_query = sql_corrector.invoke(Feedback(
            database_schema=database_schema,
            question=state.question,
            sql_query=state.sql_query,
            feedback=state.validation_result.feedback
        ))
    else:
        sql_query = sql_generator.invoke(Query(database_schema=database_schema, question=state.question))

    return {"sql_query": sql_query, "total_generations": 1}


def validation_node(state: State, config: RunnableConfig):
    """Validate the generated SQL query using repository"""
    repository = config["configurable"]["repository"]
    try:
        repository.validate_query(state.sql_query)
        validation = ValidationResult(is_valid=True)
    except ValidationError as e:
        validation = ValidationResult(is_valid=False, feedback=str(e))
    return {"validation_result": validation}


def execution_node(state: State, config: RunnableConfig):
    """Execute the validated SQL query against the database"""
    try:
        repository = config["configurable"]["repository"]
        max_rows = config["configurable"].get("max_rows", 1000)

        # Execute the query using repository
        columns, rows = repository.execute_query(state.sql_query, max_rows)

        return {
            "result": Result(
                columns=columns,
                rows=rows,
                total_rows=len(rows)
            )
        }

    except ValidationError as e:  # Specific exception for query validation errors
        return {"validation_result": ValidationResult(is_valid=False, feedback=str(e))}
    except DatabaseError as e:
        raise DatabaseFailure(f"Database error during query execution: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during query execution: {str(e)}")


def create_graph():
    """Create and compile the LangGraph workflow"""
    # Create a state graph
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("sql_generation", sql_generation_node)
    graph.add_node("validation", validation_node)
    graph.add_node("execution", execution_node)

    # Set entry point
    graph.set_entry_point("sql_generation")

    # Add conditional edges
    graph.add_conditional_edges("validation",
                                lambda state: "execution" if state.validation_result.is_valid else "sql_generation")
    graph.add_conditional_edges("execution", lambda state: END if state.result else "sql_generation")

    # Add edges
    graph.add_edge("sql_generation", "validation")

    # Compile the workflow
    return graph.compile()
