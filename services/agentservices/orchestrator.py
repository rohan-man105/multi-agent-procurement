from agents import Agent, ModelSettings
from pydantic import BaseModel
from env import nvidia_model,SETTINGS
from services.agentservices.schemas import INSTRUCTIONS_ORCH

# Output Format
class OrchestratorOutput(BaseModel):
    reply : str
    title : str
    type : str
    stop_flag : bool





# Order Modification
def orchestrator():

    orchestrator = Agent(
        name="Orchestrator",
        instructions=INSTRUCTIONS_ORCH,
        model=nvidia_model,
        model_settings=SETTINGS,
        output_type=OrchestratorOutput
    )

    return orchestrator
