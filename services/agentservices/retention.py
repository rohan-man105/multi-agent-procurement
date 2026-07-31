from agents import Agent, ModelSettings,function_tool
from agents.agent import StopAtTools
from pydantic import BaseModel
from env import nvidia_model,SETTINGS
from services.postgremanager.retrieval import run_sql_query,format_answer
from services.weaviatemanager.retrieval import get_info, format_docs
from services.agentservices.schemas import INSTRUCTIONS_RET

@function_tool
def search_by_id(product_id: str) -> str:
     sql =  f"SELECT * FROM orders WHERE transactionid = '{product_id}'"
     rows,col = run_sql_query(sql)
     return format_answer(rows,col)

@function_tool
def search_by_description(desc: str) -> str:
     """Search Weaviate semantically when user gives item name, quantity, date or any description."""
     docs = get_info(desc)
     return format_docs(docs)


# Output Format
class ModifierOutput(BaseModel):
    reply: str
    found_order: str
    user_approved: str        
    edit_field: str           
    edit_value: str           
    stop_flag: bool
    handoff_to_new: bool

# Order Modification
def modifier():

     modifier = Agent(
        name="Modifier",
        instructions=INSTRUCTIONS_RET,
        model=nvidia_model,
        tools=[search_by_id,search_by_description],
        model_settings=SETTINGS,
        output_type=ModifierOutput
    )
     
     return modifier
