"""
state.py — Única ponte entre a aplicação e o session_state do Streamlit.

O núcleo (dmaic/core) recebe estado por parâmetro. Quem lê e escreve o estado
da sessão é este módulo, para não haver dois donos do mesmo dado.
"""

from __future__ import annotations

import streamlit as st

from dmaic.core import snapshot
from dmaic.core.agent import Credenciais, Sinais, proxima_etapa
from dmaic.core.llm import PROVIDER_PADRAO
from dmaic.core.snapshot import Snapshot

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
    """
    Garante que toda chave usada pela aplicação exista e, na primeira execução
    da sessão, tenta recuperar a última sessão gravada em disco.

    Um F5 no navegador abre uma sessão nova e vazia do Streamlit. Sem esta
    recuperação, era aí que o projeto inteiro se perdia.
    """
    primeira_vez = "chat" not in st.session_state

    for chave, valor in {**PADROES_CREDENCIAIS, **PADROES_PROJETO}.items():
        if chave not in st.session_state:
            st.session_state[chave] = _copia(valor)

    if "autosave_ativo" not in st.session_state:
        st.session_state.autosave_ativo = execucao_local()
    if "restaurado_de" not in st.session_state:
        st.session_state.restaurado_de = ""

    if primeira_vez and st.session_state.autosave_ativo:
        _restaurar_autosave()


def _restaurar_autosave() -> None:
    snap = snapshot.ler_autosave()
    if snap is None:
        return
    aplicar_snapshot(snap)
    st.session_state.restaurado_de = snap.salvo_em


def reset_projeto() -> None:
    """Zera o projeto e preserva provedor, chave e modelo."""
    for chave, valor in PADROES_PROJETO.items():
        st.session_state[chave] = _copia(valor)
    st.session_state.restaurado_de = ""
    # Sem isso, o projeto abandonado voltaria no próximo F5.
    snapshot.apagar_autosave()


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


# ─────────────────────────────────────────────────────────────────
# PERSISTÊNCIA
# ─────────────────────────────────────────────────────────────────
def snapshot_atual() -> Snapshot:
    """A sessão inteira em um objeto, pronta para virar arquivo."""
    return Snapshot(
        projeto=dict(st.session_state.projeto),
        meta=dict(st.session_state.meta),
        chat=list(st.session_state.chat),
        etapa=st.session_state.etapa,
        ferramentas=list(st.session_state.ferramentas_usadas),
        aguardando_campo=bool(st.session_state.aguardando_campo),
    )


def aplicar_snapshot(snap: Snapshot) -> None:
    """Substitui a sessão pelo conteúdo do snapshot."""
    st.session_state.projeto = dict(snap.projeto)
    st.session_state.meta = dict(snap.meta)
    st.session_state.chat = list(snap.chat)
    st.session_state.etapa = snap.etapa
    st.session_state.ferramentas_usadas = list(snap.ferramentas)
    st.session_state.aguardando_campo = snap.aguardando_campo
    st.session_state.word_bytes = None
    # Projeto retomado já tem identificação, então não volta ao onboarding.
    st.session_state.pronto = bool(snap.chat or snap.meta)


def autosave() -> None:
    """
    Grava a sessão em disco quando o autosave está ligado.

    Chamado depois de cada mudança relevante. Silencioso de propósito: falha
    de escrita não pode interromper a consultoria.
    """
    if not st.session_state.get("autosave_ativo"):
        return
    snapshot.gravar_autosave(snapshot_atual())


def execucao_local() -> bool:
    """
    A aplicação está sendo acessada da própria máquina?

    O autosave grava em disco num arquivo só. Num servidor compartilhado isso
    entregaria o projeto de um usuário para o próximo, então ele só entra
    quando o acesso vem de localhost.
    """
    try:
        host = (st.context.headers.get("Host") or "").strip().lower()
    except Exception:  # versão de Streamlit sem st.context
        return False

    # Host IPv6 vem entre colchetes: "[::1]:8501".
    if host.startswith("[") and "]" in host:
        host = host[1:host.index("]")]
    else:
        host = host.split(":")[0]

    return host in ("localhost", "127.0.0.1", "::1")
