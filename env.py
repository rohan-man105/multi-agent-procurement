import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents import ModelSettings

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEYY = os.getenv("GROQ_API_KEYY")
url = "/home/ubox48/MultiAgentProject/dataset/spend_analysis_dataset.csv"

nvidia_client = AsyncOpenAI(
        api_key=OPEN_ROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
)

nvidia_model = OpenAIChatCompletionsModel(
        model="openai/gpt-4.1-mini",
        openai_client=nvidia_client
)

SETTINGS = ModelSettings(
    temperature=0.2,
    top_p=0.9,
    max_tokens=1024,
    parallel_tool_calls=False,
)