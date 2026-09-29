"""
DMAIC Agent — Consultor Six Sigma com IA
Execute: streamlit run app.py
"""

import streamlit as st

from dmaic.state import init_state
from dmaic.ui.chat import handle_user_input, render_chat, responder_se_pendente
from dmaic.ui.header import render_etapa_bar, render_header
from dmaic.ui.onboarding import render_onboarding
from dmaic.ui.sidebar import render_sidebar
from dmaic.ui.theme import CUSTOM_CSS, PAGE_CONFIG

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

init_state()

render_sidebar()
render_header()

# ── Onboarding (tela inicial) ─────────────────────────────────────
if not st.session_state.pronto:
    render_onboarding()
    st.stop()

# ── Sessão de consultoria ─────────────────────────────────────────
render_etapa_bar()
render_chat()

# A resposta é gerada depois do histórico para entrar no fim da conversa,
# em fluxo, sem duplicar a última mensagem na tela.
responder_se_pendente()
handle_user_input()
