"""
ui/onboarding.py — Tela inicial de cadastro do projeto.
"""

from __future__ import annotations

import datetime

import streamlit as st

from dmaic import state


def render_onboarding() -> None:
    """Formulário de início de projeto e primeira fala do consultor."""
    st.markdown("### Vamos começar")
    st.markdown(
        "Preencha os dados abaixo para identificar seu projeto. "
        "O consultor conduz tudo a partir daí — você não precisa saber "
        "Six Sigma."
    )

    if not state.configurado():
        st.warning(
            "Antes de iniciar, escolha o provedor e cole sua chave na barra "
            "lateral. É o que dá voz ao consultor."
        )

    with st.form("inicio"):
        c1, c2 = st.columns(2)
        empresa = c1.text_input("Empresa *")
        responsavel = c2.text_input("Responsável *")

        c3, c4 = st.columns(2)
        patrocinador = c3.text_input("Patrocinador / Sponsor")
        area = c4.text_input("Área / Departamento")

        c5, c6 = st.columns(2)
        numero = c5.text_input("Nº do Projeto")
        inicio = c6.text_input(
            "Data de Início",
            value=datetime.datetime.now().strftime("%d/%m/%Y"),
        )

        enviado = st.form_submit_button(
            "Iniciar consulta", type="primary", use_container_width=True,
            disabled=not state.configurado(),
        )

    if not enviado:
        return

    if not empresa or not responsavel:
        st.error("Empresa e Responsável são obrigatórios.")
        return

    st.session_state.meta = {
        "empresa": empresa,
        "responsavel": responsavel,
        "patrocinador": patrocinador,
        "area": area,
        "numero": numero,
        "inicio": inicio,
    }
    st.session_state.projeto["empresa"] = empresa
    st.session_state.projeto["responsavel"] = responsavel
    st.session_state.pronto = True
    st.session_state.chat = [
        {"role": "assistant", "content": _mensagem_abertura(responsavel)}
    ]
    state.autosave()
    st.rerun()


def _mensagem_abertura(responsavel: str) -> str:
    return (
        f"Olá, **{responsavel}**!\n\n"
        f"Sou seu consultor DMAIC — vou conduzir o projeto do diagnóstico até "
        f"o controle dos resultados, como um Master Black Belt faria numa "
        f"reunião real.\n\n"
        f"**Como funciono:**\n"
        f"- Faço as perguntas certas, uma de cada vez\n"
        f"- Aplico as ferramentas Six Sigma diretamente na nossa conversa — "
        f"Ishikawa, 5 Porquês, SIPOC, Pareto, FMEA e outras\n"
        f"- Quando você não tiver um dado disponível, monto um "
        f"**Plano de Campo** com as tarefas exatas para buscar essa "
        f"informação no mundo real\n"
        f"- Gero um documento Word que você leva para o campo — e quando "
        f"voltar com os dados, continuamos de onde paramos\n\n"
        f"Vamos começar: **qual é o problema que você quer resolver?** "
        f"Me conta com suas palavras, sem se preocupar com formato."
    )
