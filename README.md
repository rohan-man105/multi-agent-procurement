# Multi-Agent Procurement System

An agent-powered procurement assistant for creating new orders, renewing previous orders, searching procurement history, and analyzing spend.

The system combines a FastAPI backend, OpenAI Agents SDK workflows, PostgreSQL persistence, Weaviate semantic search, and a Streamlit frontend.

## Current status

This project is a functional multi-agent procurement foundation. It supports live persistence workflows, but it is not yet a complete enterprise procurement platform. Authentication, approval policies, ERP integrations, background jobs, and production monitoring are still planned.

## Features

- Orchestrator agent for routing new and renewal requests.
- Acquisition agent for collecting new-order details.
- Retention agent for locating previous orders by ID or description.
- PostgreSQL as the runtime source of truth for orders.
- Weaviate hybrid semantic search over procurement records.
- New order creation with validation and calculated totals.
- Renewal creation as a new row linked to the original order.
- Existing-order modification support.
- Audit events for renewals and modifications.
- CSV synchronization for analytics and export compatibility.
- Streamlit chat, spend analysis, and settings pages.
- Docker Compose setup for PostgreSQL and Weaviate.

## Architecture

```text
User
  |
  v
Streamlit Frontend
  - Chat
  - Spend analysis
  - Settings
  |
  | HTTP
  v
FastAPI Backend
  |
  v
Agent Runtime
  +-- Orchestrator
  |     Routes the request to new procurement or renewal.
  |
  +-- Acquisition Agent
  |     Collects item, category, quantity, supplier, price, and buyer.
  |
  +-- Retention Agent
        Searches previous orders and collects renewal changes.

Runtime data flow
  PostgreSQL  → authoritative order storage
       |
       +-- CSV export/analytics copy
       |
       +-- Weaviate semantic search index
```

## Order lifecycle

### New order

```text
Collect details
  → Validate quantity and price
  → Insert into PostgreSQL
  → Update CSV export
  → Upsert the order in Weaviate
```

New orders are stored with `OrderType = new`. If the price is not available, the order remains a draft instead of receiving an invented value.

### Renewal

A renewal creates a new procurement row. It does not overwrite the original order.

```text
Find original order
  → Confirm it with the user
  → Collect the changed value
  → Insert a new renewal row
  → Set ParentTransactionID to the original transaction
  → Write an audit event
  → Synchronize CSV and Weaviate
```

### Modification

An existing order can be updated directly. The original transaction ID remains the same, and an audit event records the old and new values.

## Data model

The main dataset uses these fields:

| Field | Description |
|---|---|
| `TransactionID` | Unique order identifier, such as `TXN501` |
| `OrderType` | `new`, `renewal`, or `modification` |
| `ParentTransactionID` | Original transaction ID for a renewal |
| `Status` | `draft`, `pending_approval`, `approved`, `ordered`, `completed`, or `cancelled` |
| `ItemName` | Procured item or service |
| `Category` | Procurement category |
| `Quantity` | Positive whole-number quantity |
| `UnitPrice` | Price per unit |
| `TotalCost` | Calculated as quantity × unit price |
| `PurchaseDate` | ISO-formatted purchase date |
| `Supplier` | Supplier name |
| `Buyer` | Buyer or responsible person |
| `Currency` | Currency code, currently defaulting to `USD` |

The CSV file is used to seed PostgreSQL during startup and is updated after runtime writes. PostgreSQL is the authoritative runtime store.

Audit events are stored in:

```text
PostgreSQL: order_audit_log
CSV:        dataset/order_audit_log.csv
```

## Storage and search behavior

### PostgreSQL

PostgreSQL stores exact, structured order records and handles runtime inserts and updates. The startup loader seeds the `orders` table from the CSV dataset.

### Weaviate

Weaviate is a search index, not the source of truth. It stores named vectors for:

- item name
- category
- supplier
- buyer

New and renewed orders are upserted using a stable UUID derived from their transaction ID. Modified orders replace their existing vector record. If Weaviate is temporarily unavailable, the PostgreSQL write remains authoritative and a synchronization warning is logged.

The startup synchronization rebuilds or refreshes the `Order` collection from the CSV data.

## Technology stack

| Area | Technology |
|---|---|
| Backend API | FastAPI, Uvicorn |
| Agent framework | OpenAI Agents SDK |
| Model provider | OpenRouter |
| Current configured model | `google/gemma-4-26b-a4b-it:free` |
| Structured database | PostgreSQL 16 |
| Database access | SQLAlchemy, psycopg2 |
| Vector database | Weaviate |
| Embeddings | SentenceTransformers, `all-MiniLM-L6-v2` |
| Frontend | Streamlit |
| Charts | Plotly |
| Data processing | Pandas |
| Infrastructure | Docker Compose |

## Project structure

```text
multi-agent-procurement-system/
  api/
    v1/
      chat.py                    # FastAPI chat endpoint

  dataset/
    spend_analysis_dataset.csv   # Seed/export procurement data
    order_audit_log.csv          # Generated audit export

  frontend/
    .streamlit/
      config.toml
    app.py                       # Streamlit entry point
    helpers.py                   # API and session helpers
    page_chat.py                 # Chat page
    page_settings.py             # Connection and session settings
    page_spend.py                # Spend dashboard
    requirements.txt

  services/
    agentservices/
      acquisition.py             # New-order agent and output schema
      orchestrator.py            # Routing agent
      retention.py               # Renewal agent and search tools
      run.py                     # Agent execution and persistence handoff
      schemas.py                 # Agent instructions

    postgremanager/
      load.py                    # Startup CSV-to-PostgreSQL seed
      new_order.py               # New, renewal, and modification workflows
      persistence.py             # PostgreSQL writes and audit persistence
      retrieval.py               # Parameterized SQL retrieval
      utils.py                   # Database connection setup

    weaviatemanager/
      load.py                    # Startup vector synchronization
      retrieval.py               # Hybrid semantic search
      sync.py                    # Insert/replace order embeddings
      utils.py                   # Weaviate client and embedding model

  docker-compose.yml             # PostgreSQL and Weaviate services
  env.py                         # Model and dataset configuration
  main.py                        # FastAPI application and startup lifecycle
  requirements.txt               # Backend dependencies
  ROADMAP.md                     # Stabilization and future development plan
```

## Setup

### 1. Configure environment variables

Create or update `.env` in the project root:

```env
OPEN_ROUTER_API_KEY=your_openrouter_api_key
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ecommerce
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Do not commit `.env` or real credentials.

### 2. Start PostgreSQL and Weaviate

From the project root:

```bash
docker compose up -d
```

Services:

```text
PostgreSQL:  localhost:5432
Weaviate:    localhost:8080
Weaviate gRPC: localhost:50051
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the backend

```bash
uvicorn main:app --reload
```

At startup, the application:

1. Loads the CSV seed data into PostgreSQL.
2. Creates the audit table if needed.
3. Creates or synchronizes the Weaviate `Order` collection.
4. Starts the chat API.

### 5. Start the frontend

In another terminal:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
Frontend: http://localhost:8501
Backend:  http://localhost:8000
```

## API

### Chat

```http
POST /chat/
```

Example request:

```json
{
  "message": "I want to renew my previous software license",
  "current_agent": "orchestrator",
  "history": []
}
```

Example response:

```json
{
  "response": "What would you like to title this procurement?",
  "current_agent": "orchestrator",
  "history": []
}
```

The current frontend sends the active agent and conversation history with each request. Persistent request IDs and server-side workflow state are planned improvements.

## Frontend pages

### Chat

Talk to the orchestrator, acquisition, and retention agents. The page tracks the active agent and conversation history in Streamlit session state.

### Spend Analysis

Analyzes the synchronized CSV export with filters and Plotly charts for:

- total spend
- transaction count
- average order value
- supplier spend
- category spend
- monthly trends
- top items
- buyer/category concentration

### Settings

Configures the backend URL, tests the API connection, and resets the current chat session.

## Validation and testing

Static validation currently covers:

- Python syntax for changed modules.
- Dataset schema validation.
- Transaction ID generation.
- Git whitespace checks.

Before using the system as a live application, run an end-to-end test with both containers active:

1. Create a new order.
2. Confirm the row exists in PostgreSQL.
3. Confirm it appears in the CSV export.
4. Search for it through Weaviate.
5. Create a renewal linked to the original transaction.
6. Modify an existing order.
7. Check the PostgreSQL and CSV audit logs.

## Current limitations

- Authentication and role-based permissions are not implemented.
- Supplier and buyer master data are not yet separate database entities.
- Approval rules are not yet enforced by a policy engine.
- The frontend still sends conversation history instead of using persistent workflow IDs.
- PostgreSQL and Weaviate synchronization is not yet handled by a background retry queue.
- The startup seed currently replaces the `orders` table from the CSV; production migrations should replace this behavior.
- ERP, email, accounting, CRM, and document integrations are not implemented.
- Live end-to-end validation requires PostgreSQL and Weaviate containers to be running.


## Learning objectives

This project demonstrates how multi-agent workflows can combine structured database retrieval, semantic search, validated business operations, audit logging, and a user-facing procurement interface.
