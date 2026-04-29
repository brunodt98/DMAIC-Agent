"""
state.py — Inicialização e gestão do estado da sessão Streamlit.
"""

import streamlit as st


def init_state() -> None:
    """Inicializa todas as chaves do session_state com valores padrão."""
    defaults = {
        "chat":               [],       # histórico de mensagens
        "projeto":            {},       # dados estruturados coletados
        "etapa":              "definir",
        "meta":               {},       # empresa, responsável, etc.
        "pronto":             False,    # onboarding concluído?
        "aguardando_campo":   False,    # esperando retorno do campo?
        "ferramentas_usadas": [],       # ferramentas já aplicadas na sessão
        "groq_key":           "",
        "model":              "llama-3.3-70b-versatile",
        "word_bytes":         None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    """Limpa todo o estado (novo projeto)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def set_etapa(etapa: str) -> None:
    """Avança a etapa apenas se for igual ou posterior à atual."""
    from dmaic.config import ETAPAS
    atual_idx = ETAPAS.index(st.session_state.etapa)
    novo_idx  = ETAPAS.index(etapa)
    if novo_idx >= atual_idx:
        st.session_state.etapa = etapa


def registrar_ferramenta(ferramenta: str) -> None:
    """Adiciona uma ferramenta à lista de ferramentas usadas (sem duplicatas)."""
    lista = st.session_state.get("ferramentas_usadas", [])
    if ferramenta not in lista:
        lista.append(ferramenta)
    st.session_state.ferramentas_usadas = lista
