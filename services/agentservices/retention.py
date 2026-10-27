from agents import Agent, function_tool
from pydantic import BaseModel

from env import SETTINGS, nvidia_model
from services.agentservices.schemas import INSTRUCTIONS_RET
from services.postgremanager.retrieval import format_answer, run_sql_query
from services.weaviatemanager.retrieval import format_docs, get_info


@function_tool
def search_by_id(product_id: str) -> str:
    """Find one order by transaction ID using a parameterized query."""
    rows, columns = run_sql_query(
        "SELECT * FROM orders WHERE transactionid = %s",
        (product_id.strip(),),
    )
    return format_answer(rows, columns)


@function_tool
def search_by_description(desc: str) -> str:
    """Find orders semantically from an item, supplier, date, or description."""
    return format_docs(get_info(desc))


class ModifierOutput(BaseModel):
    reply: str
    found_order: str = ""
    matched_transaction_id: str = ""
    user_approved: str = "pending"
    edit_field: str = ""
    edit_value: str = ""
    stop_flag: bool = False
    handoff_to_new: bool = False


def modifier():
    return Agent(
        name="Modifier",
        instructions=INSTRUCTIONS_RET,
        model=nvidia_model,
        tools=[search_by_id, search_by_description],
        model_settings=SETTINGS,
        output_type=ModifierOutput,
    )
