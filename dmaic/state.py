"""
state.py — Única ponte entre a aplicação e o session_state do Streamlit.

O núcleo (dmaic/core) recebe estado por parâmetro. Quem lê e escreve o estado
da sessão é este módulo, para não haver dois donos do mesmo dado.
"""

from __future__ import annotations

import streamlit as st

from dmaic.core.agent import Credenciais, Sinais, proxima_etapa
from dmaic.core.llm import PROVIDER_PADRAO

PADROES_PROJETO = {
    "chat": [],                   # histórico de mensagens exibido
    "projeto": {},                # dados estruturados apurados
    "meta": {},                   # empresa, responsável, patrocinador…
    "etapa": "definir",
    "ferramentas_usadas": [],
    "pronto": False,              # onboarding concluído?
    "aguardando_campo": False,    # esperando retorno do campo?
    "word_bytes": None,
}

# Credenciais não pertencem ao projeto: começar um projeto novo não pode
# obrigar o usuário a digitar a chave outra vez.
PADROES_CREDENCIAIS = {
    "provider": PROVIDER_PADRAO,
    "api_key": "",
    "model": "",
}


def init_state() -> None:
    """Garante que toda chave usada pela aplicação exista."""
    for chave, valor in {**PADROES_CREDENCIAIS, **PADROES_PROJETO}.items():
        if chave not in st.session_state:
            st.session_state[chave] = _copia(valor)


def reset_projeto() -> None:
    """Zera o projeto e preserva provedor, chave e modelo."""
    for chave, valor in PADROES_PROJETO.items():
        st.session_state[chave] = _copia(valor)


def _copia(valor):
    """Evita que a lista ou o dict padrão seja compartilhado entre chaves."""
    if isinstance(valor, list):
        return list(valor)
    if isinstance(valor, dict):
        return dict(valor)
    return valor


# ─────────────────────────────────────────────────────────────────
# CREDENCIAIS
# ─────────────────────────────────────────────────────────────────
def credenciais() -> Credenciais:
    return Credenciais(
        provider=st.session_state.get("provider", PROVIDER_PADRAO),
        api_key=st.session_state.get("api_key", ""),
        model=st.session_state.get("model", ""),
    )


def configurado() -> bool:
    """Há provedor, chave e modelo para conversar?"""
    return credenciais().completas()


# ─────────────────────────────────────────────────────────────────
# CONVERSA
# ─────────────────────────────────────────────────────────────────
def adicionar_mensagem(role: str, conteudo: str) -> None:
    st.session_state.chat.append({"role": role, "content": conteudo})


def aplicar_sinais(sinais: Sinais) -> None:
    """
    Atualiza etapa, ferramentas e estado de espera a partir do que o consultor
    declarou na resposta.
    """
    st.session_state.etapa = proxima_etapa(st.session_state.etapa, sinais.etapa)
    st.session_state.aguardando_campo = sinais.aguardando_campo

    usadas = st.session_state.ferramentas_usadas
    for ferramenta in sinais.ferramentas:
        if ferramenta not in usadas:
            usadas.append(ferramenta)


def atualizar_projeto(dados: dict) -> int:
    """Mescla dados apurados no projeto e devolve quantos campos entraram."""
    if not dados:
        return 0
    st.session_state.projeto.update(dados)
    return len(dados)
