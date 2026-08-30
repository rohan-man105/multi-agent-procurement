import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents import ModelSettings

load_dotenv()



OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

url = "dataset/spend_analysis_dataset.csv"

nvidia_client = AsyncOpenAI(
        api_key=OPEN_ROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
)

nvidia_model = OpenAIChatCompletionsModel(
        model="google/gemma-4-26b-a4b-it:free",
        openai_client=nvidia_client
)

SETTINGS = ModelSettings(
    temperature=0.2,
    top_p=0.9,
    max_tokens=1024,
    parallel_tool_calls=False,
)