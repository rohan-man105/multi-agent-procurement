"""
Settings page — configure the API connection and manage session.
"""

import streamlit as st
from helpers import api_get, get_api_base

_CARD_CSS = """
<style>
.settings-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 0.85rem;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.settings-card h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #E2E8F0;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.status-ok {
    background: rgba(16,185,129,0.15);
    color: #10B981;
    border: 1px solid rgba(16,185,129,0.3);
}
.status-err {
    background: rgba(239,68,68,0.15);
    color: #EF4444;
    border: 1px solid rgba(239,68,68,0.3);
}
</style>
"""


def render():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Workspace controls</div>', unsafe_allow_html=True)
    st.markdown("# Settings")
    st.markdown('<div class="page-intro">Manage the backend connection and reset the current procurement conversation.</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-card"><h4>API connection</h4>', unsafe_allow_html=True)

    new_url = st.text_input(
        "API Base URL",
        value=st.session_state.get("api_base_url", "http://localhost:8000"),
        help="The root URL of the FastAPI backend (e.g. http://localhost:8000).",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Save connection", use_container_width=True, type="primary"):
            st.session_state.api_base_url = new_url.rstrip("/")
            st.success("Saved!")

    with col2:
        if st.button("Test connection", use_container_width=True):
            with st.spinner("Testing…"):
                data = api_get("/")
            if data is not None:
                status = data.get("status", "unknown") if isinstance(data, dict) else "unknown"
                service = data.get("service", "unknown") if isinstance(data, dict) else "unknown"
                st.markdown(
                    f'<span class="status-badge status-ok">● Connected</span> '
                    f'&nbsp; Service: <code>{service}</code> &nbsp; Status: <code>{status}</code>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="status-badge status-err">● Unreachable</span>',
                    unsafe_allow_html=True,
                )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-card"><h4>Session management</h4>', unsafe_allow_html=True)
    st.markdown("Clear conversation history and reset the active agent to the default orchestrator.")

    if st.button("Reset chat session", use_container_width=False):
        st.session_state.chat_history = []
        st.session_state.current_agent = "orchestrator"
        st.session_state.agent_history = []
        st.success("Chat session cleared!")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-card"><h4>Current session</h4>', unsafe_allow_html=True)

    info_cols = st.columns(3)
    with info_cols[0]:
        st.metric("API Base URL", get_api_base())
    with info_cols[1]:
        st.metric("Active Agent", st.session_state.get("current_agent", "orchestrator"))
    with info_cols[2]:
        st.metric("Messages", len(st.session_state.get("chat_history", [])))

    st.markdown('</div>', unsafe_allow_html=True)
