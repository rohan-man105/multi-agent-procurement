# Multi-Agent Spend Analysis — Frontend

A polished **Streamlit** dashboard that connects to the existing FastAPI multi-agent backend.

## Features

| Page | Description |
|------|-------------|
| 💬 **Chat** | Conversational interface to the multi-agent system with styled chat bubbles and persistent history |
| 📊 **Spend Analysis** | Interactive Plotly charts (bar, pie, area, heatmap) with date range, category, and supplier filters |
| ⚙️ **Settings** | Configure the API base URL, test the connection, and manage session state |

## Prerequisites

- **Python 3.10+**
- The FastAPI backend running (default: `http://localhost:8000`)

## Quick Start

The full stack requires **three services** started in order:

### Step 1 — Start the databases (Docker)

From the **project root**:

```bash
docker compose up -d
```

This starts **Weaviate** (port 8080) and **PostgreSQL** (port 5432).

### Step 2 — Start the FastAPI backend

From the **project root** (in a separate terminal):

```bash
# Activate your backend venv if you have one
uvicorn main:app --reload
```

The backend starts at **http://localhost:8000**. On first launch it loads data into Postgres and creates Weaviate embeddings — wait for `Application Started Successfully` in the logs.

### Step 3 — Start the Streamlit frontend

In **another terminal**:

```bash
cd frontend

# (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

The frontend opens at **http://localhost:8501**.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Backend root URL (can also be changed in the Settings page) |

Set via environment variable:

```bash
API_BASE_URL=http://my-backend:8000 streamlit run app.py
```

Or configure interactively on the **⚙️ Settings** page.

## File Structure

```
frontend/
├── .streamlit/
│   └── config.toml       # Streamlit theme (dark mode, violet accent)
├── app.py                # Main entry-point with sidebar navigation
├── helpers.py            # API client & session-state utilities
├── page_chat.py          # Chat page module
├── page_spend.py         # Spend Analysis page module
├── page_settings.py      # Settings page module
├── requirements.txt      # Frontend-only dependencies
└── README.md             # This file
```
