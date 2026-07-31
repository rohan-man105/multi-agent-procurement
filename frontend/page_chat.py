"""
Chat page — conversational interface to the Multi-Agent backend.
"""

import streamlit as st
from helpers import api_post



_CHAT_CSS = """
<style>
/* ── Chat container ─────────────────────────────────────────────────── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-bottom: 1rem;
}
.chat-bubble {
    max-width: 80%;
    padding: 0.9rem 1.15rem;
    border-radius: 1rem;
    line-height: 1.55;
    font-size: 0.95rem;
    word-wrap: break-word;
    animation: fadeSlideIn 0.3s ease-out;
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.user-bubble {
    align-self: flex-end;
    background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
    color: #F8FAFC;
    border-bottom-right-radius: 0.25rem;
    box-shadow: 0 2px 8px rgba(124,58,237,0.25);
}
.assistant-bubble {
    align-self: flex-start;
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-bottom-left-radius: 0.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}
.bubble-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
    opacity: 0.7;
}
/* ── Typing indicator ───────────────────────────────────────────────── */
.typing-indicator span {
    display: inline-block;
    width: 7px; height: 7px;
    margin: 0 2px;
    background: #94A3B8;
    border-radius: 50%;
    animation: bounce 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-6px); }
}
</style>
"""


def _render_bubble(role: str, content: str) -> str:
    """Return HTML for a single chat bubble."""
    if role == "user":
        css_class = "user-bubble"
        label = "You"
    else:
        css_class = "assistant-bubble"
        label = "Assistant"
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br>")
    return (
        f'<div class="chat-bubble {css_class}">'
        f'<div class="bubble-label">{label}</div>'
        f'{safe}'
        f'</div>'
    )



def render():
    st.markdown(_CHAT_CSS, unsafe_allow_html=True)

    st.markdown("## 💬 Chat")
    st.caption("Ask questions about spend data, procurement insights, or anything the agents can help with.")

    if st.session_state.chat_history:
        bubbles_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            bubbles_html += _render_bubble(role, content)
        bubbles_html += '</div>'
        st.markdown(bubbles_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;opacity:0.5;">'
            '<p style="font-size:2.5rem;margin:0;">🤖</p>'
            '<p>Start a conversation by typing a message below.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Type your message…",
            label_visibility="collapsed",
        )
        col1, col2, col3 = st.columns([6, 1, 1])
        with col2:
            submitted = st.form_submit_button("Send ➤", use_container_width=True)
        with col3:
            clear = st.form_submit_button("🗑️ Clear", use_container_width=True)

    if clear:
        st.session_state.chat_history = []
        st.session_state.current_agent = "orchestrator"
        st.session_state.agent_history = []
        st.rerun()

    if submitted and user_input.strip():
        
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

        
        with st.spinner("Agent is thinking…"):
            payload = {
                "message": user_input.strip(),
                "current_agent": st.session_state.get("current_agent", "orchestrator"),
                "history": st.session_state.get("agent_history", []),
            }
            data = api_post("/chat/", payload)

        if data is not None:
            reply = data.get("response", str(data))
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.session_state.current_agent = data.get("current_agent", st.session_state.current_agent)
            st.session_state.agent_history = data.get("history", st.session_state.agent_history)
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "⚠️ Could not reach the backend. Check your connection or settings.",
            })

        st.rerun()
