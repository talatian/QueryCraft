from typing import Tuple

from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler

from sql_agent.graph import create_graph
from sql_agent.models import State
from sql_agent.repositories.base import BaseDatabaseRepository
from .repositories.factory import get_repository_for_url


class SyncAgent:
    def __init__(
            self,
            repository: BaseDatabaseRepository,
            db_table_names: Tuple[str, ...],
            max_generations: int = 3,
            callback_handler=None,
            max_rows: int = 1000
    ):
        self.callback_handler = callback_handler or CallbackHandler()
        self.repository = repository
        self.graph = create_graph()
        self.db_table_names = db_table_names
        self.max_generations = max_generations
        self.max_rows = max_rows

    @classmethod
    def with_connection_url(cls, db_connection_url: str, db_table_names: Tuple[str, ...], **kwargs):
        """Factory method to create SyncAgent with a connection URL."""

        repository = get_repository_for_url(db_connection_url)
        return cls(repository=repository, db_table_names=db_table_names, **kwargs)

    def ask(self, question) -> State:
        initial_state = State(
            question=question
        )
        return self.graph.invoke(
            input=initial_state,
            config=RunnableConfig(
                callbacks=[self.callback_handler],
                configurable={
                    "repository": self.repository,
                    "db_table_names": self.db_table_names,
                    "max_generations": self.max_generations,
                    "max_rows": self.max_rows
                }
            )
        )
