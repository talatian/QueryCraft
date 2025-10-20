import os
from typing import TypedDict

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import chain
from langchain_ollama import ChatOllama


class Query(TypedDict):
    question: str
    database_schema: str


class Feedback(TypedDict):
    question: str
    database_schema: str
    sql_query: str
    feedback: str


@chain
def sql_generation_prompt_template(inputs: Query):
    template_path = os.path.join(os.path.dirname(__file__), 'sql_generation_prompt_template.md')
    prompt = PromptTemplate.from_file(template_path)
    return prompt.invoke(inputs)


@chain
def sql_correction_prompt_template(inputs: Feedback):
    template_path = os.path.join(os.path.dirname(__file__), 'sql_correction_prompt_template.md')
    prompt = PromptTemplate.from_file(template_path)
    return prompt.invoke(inputs)


@chain
def parse(ai_message: AIMessage) -> str:
    return ai_message.content.split('</sql>')[0].strip()


model = ChatOllama(
    model=os.environ.get('OLLAMA_MODEL'),
    base_url=os.environ.get('OLLAMA_BASE_URL')
)

sql_generator = sql_generation_prompt_template | model | parse

sql_corrector = sql_correction_prompt_template | model | parse
