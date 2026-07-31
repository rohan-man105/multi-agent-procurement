"""
Shared helper utilities for the Streamlit frontend.
- API client with error handling
- Session state helpers
"""

import os
import requests
import streamlit as st


_DEFAULT_API_BASE = "http://localhost:8000"


def get_api_base() -> str:
    """Return the active API base URL (session state → env var → default)."""
    if "api_base_url" in st.session_state and st.session_state.api_base_url:
        return st.session_state.api_base_url.rstrip("/")
    return os.getenv("API_BASE_URL", _DEFAULT_API_BASE).rstrip("/")




def api_post(path: str, payload: dict, *, timeout: int = 120) -> dict | None:
    """POST to the backend. Returns parsed JSON or None on failure."""
    url = f"{get_api_base()}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"🔌 **Connection failed** — could not reach the backend at `{url}`. "
            "Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        st.error("⏱️ **Request timed out** — the backend took too long to respond.")
    except requests.exceptions.HTTPError as exc:
        st.error(f"⚠️ **HTTP {exc.response.status_code}** — {exc.response.text[:300]}")
    except Exception as exc:
        st.error(f"❌ **Unexpected error** — {exc}")
    return None


def api_get(path: str, *, params: dict | None = None, timeout: int = 30) -> dict | list | None:
    """GET from the backend. Returns parsed JSON or None on failure."""
    url = f"{get_api_base()}{path}"
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"🔌 **Connection failed** — could not reach the backend at `{url}`. "
            "Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        st.error("⏱️ **Request timed out** — the backend took too long to respond.")
    except requests.exceptions.HTTPError as exc:
        st.error(f"⚠️ **HTTP {exc.response.status_code}** — {exc.response.text[:300]}")
    except Exception as exc:
        st.error(f"❌ **Unexpected error** — {exc}")
    return None



def init_session_state():
    """Ensure all required session-state keys exist."""
    defaults = {
        "chat_history": [],          
        "current_agent": "orchestrator",
        "agent_history": [],         
        "api_base_url": os.getenv("API_BASE_URL", _DEFAULT_API_BASE),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
