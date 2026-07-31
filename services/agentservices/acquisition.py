from agents import Agent, ModelSettings
from pydantic import BaseModel
from env import nvidia_model,SETTINGS
from services.agentservices.schemas import INSTRUCTIONS_ACQ

# Output Format
class InitiatorOutput(BaseModel):
    reply: str       
    item_name: str   
    category: str    
    quantity: str    
    stop_flag: bool 

# New Orders
def initiation():

    initiator = Agent(
    name="Initiator",
    instructions=INSTRUCTIONS_ACQ,
    model=nvidia_model,
    model_settings=SETTINGS,
    output_type=InitiatorOutput
    )

    return initiator
