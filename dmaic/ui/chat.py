"""
ui/chat.py — Histórico da conversa, entrada do usuário e resposta em fluxo.

A resposta do consultor termina com um rodapé de marcadores que a aplicação
usa para saber a etapa e as ferramentas. Ele é filtrado antes de chegar à
tela: o usuário nunca deve ver o maquinário.
"""

from __future__ import annotations

import re
from typing import Iterator

import streamlit as st

from dmaic import state
from dmaic.core import agent
from dmaic.core.export.word import gerar_word
from dmaic.core.llm import LLMError

# Ícones Material do próprio Streamlit. Um caractere que não seja emoji — "◉",
# por exemplo — é interpretado como caminho de imagem e derruba o chat.
AVATAR_CONSULTOR = ":material/support_agent:"
AVATAR_USUARIO = ":material/person:"

_RE_RODAPE = re.compile(
    r"\[\s*(?:ETAPA|FERRAMENTAS?|AGUARDANDO[_ ]CAMPO)\s*:[^\]]*\]\s*", re.I)


def render_chat() -> None:
    """Exibe todo o histórico de mensagens."""
    for msg in st.session_state.chat:
        avatar = AVATAR_CONSULTOR if msg["role"] == "assistant" else AVATAR_USUARIO
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def handle_user_input() -> None:
    """Captura a mensagem do usuário e devolve o controle para exibi-la."""
    texto = st.chat_input("Responda ou faça uma pergunta...")
    if not texto or not texto.strip():
        return

    state.adicionar_mensagem("user", texto.strip())
    # O usuário voltou a falar: some com o aviso de espera antes de responder.
    st.session_state.aguardando_campo = False
    st.rerun()


def responder_se_pendente() -> None:
    """
    Responde quando a última mensagem é do usuário.

    Fazer isso aqui, e não dentro do handler da entrada, mantém uma única
    ordem de renderização: histórico primeiro, resposta nova no fim.
    """
    chat = st.session_state.chat
    if not chat or chat[-1]["role"] != "user":
        return

    mensagens = agent.montar_mensagens(
        chat=chat,
        projeto=st.session_state.projeto,
        etapa=st.session_state.etapa,
        ferramentas=st.session_state.ferramentas_usadas,
        aguardando=st.session_state.aguardando_campo,
        meta=st.session_state.meta,
    )

    with st.chat_message("assistant", avatar=AVATAR_CONSULTOR):
        bruto: list[str] = []
        try:
            pedacos = _capturar(agent.responder_stream(state.credenciais(), mensagens),
                                bruto)
            st.write_stream(_sem_rodape(pedacos))
        except LLMError as erro:
            st.error(str(erro))
            if not bruto:
                return

    resposta = "".join(bruto)
    if not resposta.strip():
        st.warning("O modelo devolveu uma resposta vazia. Tente enviar de novo.")
        return

    sinais = agent.ler_sinais(resposta)
    state.adicionar_mensagem("assistant", sinais.texto)
    state.aplicar_sinais(sinais)

    if sinais.aguardando_campo:
        _preparar_documento_de_campo()

    st.rerun()


# ─────────────────────────────────────────────────────────────────
# FLUXO DE TEXTO
# ─────────────────────────────────────────────────────────────────
def _capturar(pedacos: Iterator[str], destino: list[str]) -> Iterator[str]:
    """Repassa o fluxo guardando o texto bruto, marcadores incluídos."""
    for pedaco in pedacos:
        destino.append(pedaco)
        yield pedaco


def _sem_rodape(pedacos: Iterator[str]) -> Iterator[str]:
    """
    Fluxo sem o rodapé de controle.

    Segura o texto a partir de um "[" em início de linha — onde o rodapé
    começa — para o marcador não piscar na tela antes de ser removido. Se o
    que ficou retido não era rodapé, sai no fim, inteiro.
    """
    retido = ""
    for pedaco in pedacos:
        retido += pedaco
        corte = retido.find("\n[")
        if corte == -1:
            yield retido
            retido = ""
        elif corte > 0:
            yield retido[:corte]
            retido = retido[corte:]

    resto = _RE_RODAPE.sub("", retido).rstrip()
    if resto:
        yield resto


# ─────────────────────────────────────────────────────────────────
# PROTOCOLO DE CAMPO
# ─────────────────────────────────────────────────────────────────
def _preparar_documento_de_campo() -> None:
    """
    Ao emitir o Plano de Campo, apura os dados e deixa o .docx pronto.

    Falha aqui não pode derrubar a conversa: o usuário ainda pode gerar o
    documento manualmente pela barra lateral.
    """
    with st.spinner("Preparando o documento de campo..."):
        try:
            dados = agent.extrair_dados(state.credenciais(), st.session_state.chat)
            state.atualizar_projeto(dados)
        except LLMError as erro:
            st.warning(f"Não consegui apurar os dados agora: {erro}")

        try:
            st.session_state.word_bytes = gerar_word(
                projeto=st.session_state.projeto,
                meta=st.session_state.meta,
                chat=st.session_state.chat,
                etapa=st.session_state.etapa,
                ferramentas=st.session_state.ferramentas_usadas,
            )
        except Exception as erro:  # python-docx falha de formas variadas
            st.warning(f"Não consegui montar o Word agora: {erro}")
            return

    st.toast("Documento de campo pronto — baixe na barra lateral.", icon="📄")
