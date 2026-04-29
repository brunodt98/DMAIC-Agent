"""
DMAIC Agent — Consultor Six Sigma com IA
Execute: streamlit run app.py
"""

import streamlit as st

from dmaic.config import PAGE_CONFIG, CUSTOM_CSS
from dmaic.state import init_state
from dmaic.ui.sidebar import render_sidebar
from dmaic.ui.header import render_header, render_etapa_bar
from dmaic.ui.chat import render_chat, handle_user_input
from dmaic.ui.onboarding import render_onboarding

# ── Configuração da página ────────────────────────────────────────
st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Estado global ─────────────────────────────────────────────────
init_state()

# ── Sidebar (sempre visível) ──────────────────────────────────────
render_sidebar()

# ── Cabeçalho ─────────────────────────────────────────────────────
render_header()

# ── Onboarding (tela inicial) ─────────────────────────────────────
if not st.session_state.pronto:
    render_onboarding()
    st.stop()

# ── Barra de progresso DMAIC ──────────────────────────────────────
render_etapa_bar()

# ── Chat principal ────────────────────────────────────────────────
render_chat()
handle_user_input()
