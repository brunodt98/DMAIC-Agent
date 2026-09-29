"""
ui/header.py — Marca da aplicação e trilha de progresso pelas etapas.

A trilha é marcação própria, e não caixas nativas do Streamlit, por dois
motivos: as caixas não se conectam, então não se lê como uma sequência; e cada
uma vem com a cor e o espaçamento do componente, não do projeto.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from dmaic.core.metodo import ETAPAS, ETAPAS_META, indice_etapa


def render_header() -> None:
    """Marca e, quando há projeto em curso, a identificação à direita."""
    st.markdown(_marca_html(), unsafe_allow_html=True)


def _marca_html() -> str:
    barras = "".join("<i></i>" for _ in ETAPAS)
    return f"""
<div class="dmaic-marca">
  <div class="dmaic-glifo">{barras}</div>
  <div>
    <div class="dmaic-marca-nome">DMAIC Agent</div>
    <div class="dmaic-marca-sub">Consultor Six Sigma · FATEC Cotia × Outtech Services IT</div>
  </div>
  {_contexto_html()}
</div>"""


def _contexto_html() -> str:
    """Empresa e responsável no canto, para saber de qual projeto se trata."""
    if not st.session_state.get("pronto"):
        return ""
    meta = st.session_state.get("meta") or {}
    empresa = escape(str(meta.get("empresa", "")))
    responsavel = escape(str(meta.get("responsavel", "")))
    if not empresa and not responsavel:
        return ""
    linhas = []
    if empresa:
        linhas.append(f"<b>{empresa}</b>")
    if responsavel:
        linhas.append(responsavel)
    return f'<div class="dmaic-marca-ctx">{"<br>".join(linhas)}</div>'


def render_etapa_bar() -> None:
    """Trilha das cinco etapas, com o traço aceso até onde o projeto chegou."""
    atual = indice_etapa(st.session_state.etapa)

    passos = []
    for i, etapa in enumerate(ETAPAS):
        meta = ETAPAS_META[etapa]
        if i < atual:
            estado, selo = "feito", "✓"
        elif i == atual:
            estado, selo = "atual", meta["letra"]
        else:
            estado, selo = "adiante", meta["letra"]

        passos.append(
            f'<div class="dmaic-passo {estado}">'
            f'<div class="dmaic-selo">{selo}</div>'
            f'<span class="dmaic-nome">{escape(meta["label"])}</span>'
            f'<span class="dmaic-dica">{escape(meta["resumo"])}</span>'
            f"</div>"
        )

    st.markdown(
        f'<div class="dmaic-trilha">{"".join(passos)}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("aguardando_campo"):
        st.markdown(
            '<div class="dmaic-faixa">'
            '<div class="dmaic-faixa-borda"></div>'
            "<div><b>Aguardando dados do campo.</b> Quando retornar com as "
            "informações, continue a conversa normalmente — ou carregue o "
            "projeto salvo na barra lateral.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.write("")
