from typing import List, Tuple

from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler

from sql_agent.graph import create_graph
from sql_agent.models import State

class SyncAgent:
    def __init__(
            self,
            db_connection_url: str,
            db_table_names: Tuple[str, ...],
            max_generations: int = 3,
            callback_handler=None,
            max_rows: int = 1000
    ):
        self.callback_handler = callback_handler or CallbackHandler()
        self.graph = create_graph()
        self.db_connection_url = db_connection_url
        self.db_table_names = db_table_names
        self.max_generations = max_generations
        self.max_rows = max_rows

    def ask(self, question) -> State:
        initial_state = State(
            question=question
        )
        return self.graph.invoke(
            input=initial_state,
            config=RunnableConfig(
                callbacks=[self.callback_handler],
                configurable={
                    "db_connection_url": self.db_connection_url,
                    "db_table_names": self.db_table_names,
                    "max_generations": self.max_generations,
                    "max_rows": self.max_rows
                }
            )
        )
