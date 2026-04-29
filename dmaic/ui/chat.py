"""
ui/chat.py — Renderização do histórico de chat e tratamento de input do usuário.
"""

import streamlit as st

from dmaic.ai import ai_chat, extrair_dados, detectar_ferramentas, detectar_etapa
from dmaic.document import gerar_word
from dmaic.state import set_etapa, registrar_ferramenta
from dmaic.config import ETAPAS


def render_chat() -> None:
    """Exibe todo o histórico de mensagens."""
    for msg in st.session_state.chat:
        avatar = "🎯" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def handle_user_input() -> None:
    """Captura o input, chama a IA e atualiza o estado."""
    user_text = st.chat_input("Responda ou faça uma pergunta...")

    if not user_text or not user_text.strip():
        return

    # Usuário respondeu → não está mais aguardando campo
    if st.session_state.get("aguardando_campo"):
        st.session_state.aguardando_campo = False

    # Exibe mensagem do usuário
    st.session_state.chat.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_text)

    # Chama o consultor
    with st.chat_message("assistant", avatar="🎯"):
        with st.spinner("Consultando..."):
            resposta = ai_chat()
        st.markdown(resposta)

    st.session_state.chat.append({"role": "assistant", "content": resposta})

    # ── Pós-processamento da resposta ─────────────────────────────
    _atualizar_etapa(resposta)
    _registrar_ferramentas(resposta)
    _acionar_protocolo_campo(resposta)

    st.rerun()


# ─────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────────────────────────
def _atualizar_etapa(resposta: str) -> None:
    """Detecta e avança a etapa com base na resposta do agente."""
    nova = detectar_etapa(st.session_state.chat)
    set_etapa(nova)


def _registrar_ferramentas(resposta: str) -> None:
    """Detecta e registra ferramentas aplicadas na resposta."""
    for ferramenta in detectar_ferramentas(resposta):
        registrar_ferramenta(ferramenta)


def _acionar_protocolo_campo(resposta: str) -> None:
    """
    Quando o agente gera um Plano de Campo:
    - Marca que está aguardando retorno
    - Extrai dados da conversa
    - Gera o documento Word automaticamente
    - Exibe um toast ao usuário
    """
    if "plano de campo" not in resposta.lower():
        return

    st.session_state.aguardando_campo = True

    with st.spinner("📄 Gerando documento de campo..."):
        dados = extrair_dados(st.session_state.chat)
        if dados:
            st.session_state.projeto.update(dados)
        st.session_state.word_bytes = gerar_word()

    st.toast(
        "📄 Documento pronto! Clique em **Baixar .docx** na barra lateral.",
        icon="✅",
    )
