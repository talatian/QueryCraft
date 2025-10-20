import logging

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, IntegrityError, DataError

from sql_agent.exceptions import DatabaseError, AgentFailure
from sql_agent.models import State, Result, ValidationResult
from sql_agent.sql_coder.generator import sql_generator, Query, Feedback, sql_corrector
from sql_agent.utils import extract_table_metadata_ddl, validate_sql_query

logger = logging.getLogger(__name__)


def sql_generation_node(state: State, config: RunnableConfig):
    """Generate SQL query from natural language question using Ollama"""

    if state.total_generations >= config["configurable"]["max_generations"]:
        raise AgentFailure("Agent could not answer the question")

    # Get the current database schema
    database_schema = extract_table_metadata_ddl(
        connection_url=config["configurable"]["db_connection_url"],
        table_names=config["configurable"]["db_table_names"]
    )

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
    """Validate the generated SQL query"""

    validation = validate_sql_query(state.sql_query)
    return {"validation_result": validation}


def execution_node(state: State, config: RunnableConfig):
    """Execute the validated SQL query against the database"""

    try:
        # Create SQLAlchemy engine
        engine = create_engine(config["configurable"]["db_connection_url"])

        # Execute the query
        with engine.connect() as conn:
            result = conn.execute(text(state.sql_query))

            # Get column names and rows
            columns = result.keys()
            rows = result.fetchmany(config["configurable"].get("max_rows", 1000))

            return {
                "result": Result(
                    columns=list(columns),
                    rows=[list(row) for row in rows],
                    total_rows=len(rows)
                )
            }

    except (ProgrammingError, IntegrityError, DataError) as e:
        return {"validation_result": ValidationResult(is_valid=False, feedback=str(e))}
    except SQLAlchemyError as e:
        raise DatabaseError(f"Database error during query execution: {str(e)}")


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
