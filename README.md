# Multi-Agent Procurement System

This is a procurement assistant I built to experiment with multi-agent workflows, structured data retrieval, and semantic search in one project. The idea is simple: a user should be able to talk to the system in natural language, and the backend should decide whether the request is for a new procurement order or a renewal of an existing one.

The project combines a FastAPI backend, OpenAI Agents SDK based agents, PostgreSQL for exact order lookup, Weaviate for semantic search, and a Streamlit frontend for chat and spend analysis.

## Why I Built This

Procurement workflows usually involve a mix of structured information and messy user input. A user may know the exact transaction ID, or they may only remember something like "the laptop order from last quarter". I wanted to build a system that can handle both cases:

- exact lookup through PostgreSQL
- semantic lookup through Weaviate
- agent routing based on user intent
- a simple frontend for testing the full flow
- a spend dashboard to explore the procurement dataset

## Main Features

- Multi-agent conversation flow for procurement requests
- Orchestrator agent that decides where the user should go next
- Acquisition agent for collecting details for a new order
- Retention agent for finding and renewing previous orders
- PostgreSQL storage for structured procurement records
- Weaviate vector search for natural-language order lookup
- FastAPI endpoint for chat interaction
- Streamlit frontend with chat, settings, and spend dashboard pages
- Docker Compose setup for PostgreSQL and Weaviate

## Architecture

```text
User
  |
  v
Streamlit Frontend
  - Chat page
  - Spend analysis page
  - Settings page
  |
  | HTTP request
  v
FastAPI Backend
  |
  v
Agent Runtime
  |
  +-- Orchestrator Agent
  |     - collects the user's procurement need
  |     - asks for a title
  |     - decides if it is a new order or renewal
  |
  +-- Acquisition Agent
  |     - handles new procurement requests
  |     - collects item name, category, and quantity
  |
  +-- Retention Agent
        - handles renewal requests
        - searches by transaction ID using PostgreSQL
        - searches by description using Weaviate
        - asks the user what they want to update

Data Layer
  |
  +-- PostgreSQL
  |     - stores the CSV data as an orders table
  |     - used for exact transaction ID search
  |
  +-- Weaviate
        - stores vector embeddings for order fields
        - used for semantic search on item/category/supplier/buyer
```

## How The Flow Works

1. The user starts a conversation from the Streamlit chat page.
2. The FastAPI backend sends the message to the current active agent.
3. The Orchestrator first asks what the user wants to procure, what title to give the request, and whether it is a new order or a renewal.
4. If it is a new order, the conversation moves to the Acquisition Agent.
5. If it is a renewal, the conversation moves to the Retention Agent.
6. The Retention Agent can search previous orders in two ways:
   - by transaction ID through PostgreSQL
   - by natural-language description through Weaviate
7. The backend returns the agent reply and updated conversation state to the frontend.

## Tech Stack

| Part | Technology |
|------|------------|
| Backend API | FastAPI, Uvicorn |
| Agent framework | OpenAI Agents SDK |
| LLM provider | OpenRouter with GPT-4.1 Mini |
| SQL database | PostgreSQL 16 |
| Vector database | Weaviate |
| Embeddings | SentenceTransformers, all-MiniLM-L6-v2 |
| Frontend | Streamlit |
| Charts | Plotly |
| Data handling | Pandas |
| Infrastructure | Docker Compose |

## Project Structure

```text
multi-agent-procurement-system/
  api/
    v1/
      chat.py                 # FastAPI chat endpoint

  dataset/
    spend_analysis_dataset.csv

  frontend/
    .streamlit/
      config.toml             # Streamlit theme config
    app.py                    # Streamlit entry point
    helpers.py                # API and session-state helpers
    page_chat.py              # Chat UI
    page_settings.py          # Backend URL and session controls
    page_spend.py             # Spend dashboard
    requirements.txt
    README.md

  services/
    agentservices/
      acquisition.py          # New-order agent
      orchestrator.py         # Routing agent
      retention.py            # Renewal/search agent
      run.py                  # Agent runner and handoff logic
      schemas.py              # Agent instructions/prompts

    postgremanager/
      load.py                 # Loads CSV into PostgreSQL
      retrieval.py            # SQL query and formatting helpers
      utils.py                # PostgreSQL connection setup

    weaviatemanager/
      load.py                 # Creates Weaviate collection and embeddings
      retrieval.py            # Hybrid semantic search
      utils.py                # Weaviate client and embedding model

  docker-compose.yml          # PostgreSQL and Weaviate services
  env.py                      # API/model configuration
  main.py                     # FastAPI app startup
  requirements.txt            # Backend dependencies
```

## Dataset

The project uses `dataset/spend_analysis_dataset.csv`, which contains procurement transaction records with fields like:

| Field | Example |
|-------|---------|
| TransactionID | TXN001 |
| ItemName | Desk Chair |
| Category | Furniture |
| Quantity | 10 |
| UnitPrice | 113.15 |
| TotalCost | 1131.50 |
| PurchaseDate | 2024-04-19 |
| Supplier | TechMart Inc. |
| Buyer | Kelly Joseph |

When the backend starts, the dataset is loaded into PostgreSQL. The same dataset is also embedded into Weaviate so the retention agent can search previous orders from natural-language descriptions.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/rohan-man105/multi-agent-procurement.git
cd multi-agent-procurement
```

### 2. Create a `.env` file

```env
OPEN_ROUTER_API_KEY=your_openrouter_api_key
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ecommerce
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

`OPENAI_API_KEY` and `GROQ_API_KEY` can also be added if you want to experiment with other providers later, but the current setup uses OpenRouter.

### 3. Start PostgreSQL and Weaviate

```bash
docker compose up -d
```

This starts:

- PostgreSQL on port `5432`
- Weaviate on port `8080`
- Weaviate gRPC on port `50051`

### 4. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the backend

```bash
uvicorn main:app --reload
```

On startup, the backend loads the dataset into PostgreSQL and creates embeddings in Weaviate.

### 6. Run the frontend

Open a second terminal:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

The frontend runs at:

```text
http://localhost:8501
```

The backend runs at:

```text
http://localhost:8000
```

## API Endpoint

The backend currently exposes one main chat endpoint.

```http
POST /chat/
```

Example request:

"""json
{
  "message": "I want to renew my previous chair order",
  "current_agent": "orchestrator",
  "history": []
}
"""
Example response:

"""json
{
  "response": "What would you like to title this procurement?",
  "current_agent": "orchestrator",
  "history": []
}
"""

The frontend keeps passing 'current_agent' and 'history' back to the backend so the conversation can continue with the right agent.

## Frontend Pages

**Chat**

Used for talking to the procurement agents. It stores the current agent, chat messages, and backend conversation history in Streamlit session state.

**Spend Analysis**

Loads the procurement CSV and shows dashboard views such as total spend, transactions, average order value, category spend, supplier spend, monthly trends, and top items.

**Settings**

Lets the user configure the backend API URL, test the backend connection, and reset the current chat session.

## Current Limitations

- The project currently focuses on the conversation and retrieval flow, not actual database updates after a renewal.
- The CSV path in 'env.py' is currently configured for my local setup and may need to be changed if the project is moved.
- Weaviate embeddings are recreated from the dataset during startup if the collection does not already exist.
- Authentication and user accounts are not included yet.

## Future Improvements

- Add real order update/write-back after the Retention Agent confirms changes
- Make the dataset path fully relative instead of machine-specific
- Add tests for agent routing and retrieval tools
- Add API endpoints for spend dashboard data instead of reading CSV directly in the frontend
- Add authentication for multi-user usage
- Improve deployment setup for cloud hosting

## What I Learned

This project helped me connect multiple moving parts into one workflow: agents, API design, SQL retrieval, vector search, Docker services, and frontend state handling. The most interesting part was designing the handoff flow between agents so that each agent has a small, clear responsibility instead of making one large assistant do everything.
