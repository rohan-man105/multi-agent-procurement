"""
Multi-Agent Spend Analysis — Streamlit Frontend
=================================================
A polished single-page Streamlit application that provides:
  • Chat interface to interact with the multi-agent backend
  • Spend Analysis dashboards with interactive Plotly charts
  • Settings panel for API configuration & session management
"""

import streamlit as st
from helpers import init_session_state


st.set_page_config(
    page_title="Multi-Agent Spend Analysis",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()


st.markdown(
    """
    <style>
    /* ── Import Inter from Google Fonts ───────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* ── Sidebar ─────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: 1px solid #334155;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-weight: 500;
    }

    /* ── Sidebar nav items ───────────────────────────────────────── */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.65rem 1rem;
        border-radius: 0.6rem;
        margin-bottom: 0.25rem;
        transition: background 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        color: #CBD5E1;
        text-decoration: none;
    }
    .nav-item:hover {
        background: rgba(124,58,237,0.12);
        color: #E2E8F0;
    }

    /* ── Hide default Streamlit branding ──────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Scroll-to-bottom for chat ───────────────────────────────── */
    .block-container {
        padding-top: 1.5rem;
    }

    /* ── Custom title ────────────────────────────────────────────── */
    .app-title {
        font-size: 1.35rem;
        font-weight: 700;
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.78rem;
        color: #64748B;
        margin-bottom: 1.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="app-title">🧠 Multi-Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Spend Analysis Platform</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        options=["💬  Chat", "📊  Spend Analysis", "⚙️  Settings"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;padding:0 0.5rem;">'
        "Connected to:<br>"
        f'<code style="color:#7C3AED;font-size:0.72rem;">{st.session_state.get("api_base_url", "")}</code>'
        "</div>",
        unsafe_allow_html=True,
    )


if page.startswith("💬"):
    import page_chat
    page_chat.render()

elif page.startswith("📊"):
    import page_spend
    page_spend.render()

elif page.startswith("⚙️"):
    import page_settings
    page_settings.render()
