# import asyncio
# from services.postgremanager.load import sql_load
# from services.weaviatemanager.load import create_embeddings
# from services.agentservices.run import handle_turn


# async def main():

#     sql_load()
#     create_embeddings()


#     current_agent = "orchestrator"
#     history = []

#     response, current_agent, history = await handle_turn(current_agent, history, "")
#     print(f"\nAssistant: {response}\n")

#     while True:
#         user_input = input("YOU: ").strip()

#         if user_input.lower() in ["exit", "quit"]:
#             break

#         response, current_agent, history = await handle_turn(current_agent, history, user_input)
#         print(f"\nAssistant: {response}\n")


# if __name__ == "__main__":
#     asyncio.run(main())

from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.postgremanager.load import sql_load
from services.weaviatemanager.load import create_embeddings

from api.v1.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Loading PostgreSQL Data...")
    sql_load()

    print("Loading Weaviate Embeddings...")
    create_embeddings()

    print("Application Started Successfully")

    yield

    print("Application Shutdown")


app = FastAPI(
    title="Multi Agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "multi-agent-api"
    }