from agents import Agent
from pydantic import BaseModel

from env import SETTINGS, nvidia_model
from services.agentservices.schemas import INSTRUCTIONS_ACQ


class InitiatorOutput(BaseModel):
    reply: str
    item_name: str = ""
    category: str = ""
    quantity: str = ""
    supplier: str = ""
    unit_price: str = ""
    buyer: str = ""
    stop_flag: bool = False


def initiation():
    return Agent(
        name="Initiator",
        instructions=INSTRUCTIONS_ACQ,
        model=nvidia_model,
        model_settings=SETTINGS,
        output_type=InitiatorOutput,
    )
