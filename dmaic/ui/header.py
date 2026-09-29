"""
ui/header.py — Cabeçalho da aplicação e barra de progresso DMAIC.
"""

import streamlit as st

from dmaic.core.metodo import ETAPAS, ETAPAS_META, indice_etapa


def render_header() -> None:
    st.markdown("# DMAIC Agent")
    st.caption("Consultor Six Sigma com IA · FATEC Cotia × Outtech Services IT")


def render_etapa_bar() -> None:
    """Barra de 5 colunas mostrando o progresso pelas etapas DMAIC."""
    atual_i = indice_etapa(st.session_state.etapa)
    cols = st.columns(5)

    for i, (etapa, col) in enumerate(zip(ETAPAS, cols)):
        meta = ETAPAS_META[etapa]
        rotulo = f"{meta['letra']} · {meta['label']}"
        with col:
            if i < atual_i:
                st.success(rotulo)
            elif i == atual_i:
                st.info(f"**{rotulo}**")
            else:
                st.markdown(
                    f"<div style='background:#1e2a3a;border-radius:8px;padding:8px;"
                    f"text-align:center;color:#556;font-size:.85rem;'>"
                    f"{rotulo}</div>",
                    unsafe_allow_html=True,
                )

    if st.session_state.get("aguardando_campo"):
        st.warning(
            "**Aguardando dados do campo.** Quando retornar com as "
            "informações, continue a conversa normalmente — ou carregue o "
            ".docx preenchido na barra lateral."
        )

    st.divider()
