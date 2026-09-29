"""
ui/sidebar.py — Provedor e modelo, retomada de projeto, progresso e exportação.
"""

from __future__ import annotations

import datetime
import io
import json
from html import escape

import streamlit as st

from dmaic import state
from dmaic.core import agent, llm, snapshot
from dmaic.core.export.word import gerar_word, nome_arquivo
from dmaic.core.llm import PROVIDERS, LLMError
from dmaic.core.snapshot import SnapshotInvalido
from dmaic.core.metodo import (
    ETAPAS,
    ETAPAS_META,
    campo_meta_por_label,
    campo_por_label,
    indice_etapa,
)


def _secao(titulo: str) -> None:
    """Título de seção da lateral — menor e mais discreto que um heading."""
    st.markdown(f'<div class="dmaic-secao">{titulo}</div>',
                unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        _secao("Conexão")
        _render_conexao()

        st.divider()
        _secao("Projeto")
        _render_projeto()

        if st.session_state.pronto:
            st.divider()
            _secao("Progresso")
            _render_status()

            st.divider()
            _secao("Documento")
            _render_export()

        st.divider()
        _secao("Retomar de um Word")
        _render_retomada()

        st.divider()
        if st.button("Novo projeto", use_container_width=True):
            state.reset_projeto()
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# CONEXÃO COM O PROVEDOR
# ─────────────────────────────────────────────────────────────────
def _ao_trocar_provedor() -> None:
    """Modelo de um provedor não existe no outro — zera a escolha."""
    st.session_state.model = ""
    llm.limpar_cache_modelos()


def _render_conexao() -> None:
    ids = list(PROVIDERS)
    st.selectbox(
        "Provedor",
        ids,
        key="provider",
        format_func=lambda i: PROVIDERS[i].label,
        on_change=_ao_trocar_provedor,
    )
    prov = PROVIDERS[st.session_state.provider]

    st.text_input(
        f"Chave da {prov.label}",
        type="password",
        key="api_key",
        placeholder=f"{prov.key_prefix}...",
        help=f"Crie uma chave gratuita em {prov.keys_url}",
    )

    if not st.session_state.api_key:
        st.info(f"Cole sua chave da {prov.label} para começar.")
        st.markdown(f"[Obter chave →]({prov.keys_url})")
        st.session_state.model = ""
        return

    _render_seletor_modelo(prov)


def _render_seletor_modelo(prov) -> None:
    """Modelos que a chave alcança, buscados no provedor."""
    try:
        modelos = llm.validar_chave(st.session_state.provider,
                                    st.session_state.api_key)
    except LLMError as erro:
        st.error(str(erro))
        st.session_state.model = ""
        return

    ids = [m.id for m in modelos]
    if st.session_state.model not in ids:
        st.session_state.model = llm.modelo_padrao(modelos)

    rotulos = {m.id: m.descricao() for m in modelos}
    st.selectbox(
        "Modelo",
        ids,
        key="model",
        format_func=lambda i: rotulos.get(i, i),
    )
    st.caption(f"Conectado · {len(ids)} modelos disponíveis nesta chave")


# ─────────────────────────────────────────────────────────────────
# ARQUIVO DE PROJETO
# ─────────────────────────────────────────────────────────────────
def _render_projeto() -> None:
    if st.session_state.restaurado_de:
        st.caption(f"Sessão recuperada de {_data_curta(st.session_state.restaurado_de)}")

    if st.session_state.pronto:
        snap = state.snapshot_atual()
        st.download_button(
            "Salvar projeto",
            data=snapshot.para_bytes(snap),
            file_name=snapshot.nome_arquivo(snap),
            mime="application/json",
            use_container_width=True,
            help="Baixa o projeto inteiro — conversa, dados e etapa — para "
                 "abrir depois em qualquer máquina.",
        )

    arquivo = st.file_uploader(
        f"Abrir projeto ({snapshot.EXTENSAO})",
        type=["json"],
        key="upload_projeto",
        help="Arquivo salvo por esta aplicação.",
    )
    if arquivo is not None:
        _abrir_projeto(arquivo)

    _render_autosave()


def _abrir_projeto(arquivo) -> None:
    try:
        snap = snapshot.de_bytes(arquivo.read())
    except SnapshotInvalido as erro:
        st.error(str(erro))
        return

    if snap.vazio():
        st.error("Esse arquivo não tem nenhum projeto dentro.")
        return

    st.caption(f"{snap.descricao()} · {len(snap.chat)} mensagens")
    if not st.button("Abrir este projeto", use_container_width=True,
                     type="primary"):
        return

    state.aplicar_snapshot(snap)
    st.session_state.restaurado_de = snap.salvo_em
    state.autosave()
    st.rerun()


def _render_autosave() -> None:
    """
    Controle do autosave. Só aparece quando a aplicação roda localmente: num
    servidor compartilhado, gravar a sessão em disco misturaria os projetos de
    usuários diferentes.
    """
    if not state.execucao_local():
        st.caption(
            "Autosave indisponível em acesso remoto — salve o projeto em "
            "arquivo antes de fechar."
        )
        return

    st.toggle(
        "Recuperar sessão após F5",
        key="autosave_ativo",
        help=f"Grava a sessão em {snapshot.diretorio_dados()} a cada resposta.",
    )


def _data_curta(iso: str) -> str:
    """Data ISO no formato que se lê de relance."""
    try:
        return datetime.datetime.fromisoformat(iso).strftime("%d/%m às %H:%M")
    except ValueError:
        return iso[:16]


# ─────────────────────────────────────────────────────────────────
# RETOMAR PROJETO A PARTIR DO WORD
# ─────────────────────────────────────────────────────────────────
def _ler_docx(file_bytes: bytes) -> dict:
    """
    Campos e texto de um .docx gerado pela própria ferramenta.

    As tabelas são pares rótulo → valor, então os rótulos voltam a ser nomes
    de campo. Sem essa tradução o projeto retomado ficava com chaves que o
    gerador do Word não reconhece, e o documento seguinte saía em branco.
    """
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    campos: dict[str, str] = {}
    identificacao: dict[str, str] = {}
    avulsos: dict[str, str] = {}

    for tabela in doc.tables:
        for linha in tabela.rows:
            if len(linha.cells) < 2:
                continue
            rotulo = linha.cells[0].text.strip()
            valor = linha.cells[1].text.strip()
            if not rotulo or not valor or valor in ("Não informado", "—"):
                continue
            if campo := campo_por_label(rotulo):
                campos[campo] = valor
            elif campo := campo_meta_por_label(rotulo):
                identificacao[campo] = valor
            else:
                avulsos[rotulo[:60]] = valor

    # A capa traz "EMPRESA  |  DMAIC PROJECT CHARTER" numa célula só.
    for tabela in doc.tables:
        primeira = tabela.rows[0].cells[0].text
        if "DMAIC PROJECT CHARTER" in primeira:
            empresa = primeira.split("|")[0].strip()
            if empresa:
                identificacao.setdefault("empresa", empresa)
            break

    texto = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return {
        "campos": campos,
        "identificacao": identificacao,
        "avulsos": avulsos,
        "texto": texto[:4000],
    }


def _render_retomada() -> None:
    enviado = st.file_uploader(
        "Carregar .docx gerado anteriormente",
        type=["docx"],
        label_visibility="collapsed",
    )
    if not enviado:
        return

    if not state.configurado():
        st.warning("Configure a chave antes de retomar um projeto.")
        return

    if not st.button("Carregar e continuar", use_container_width=True):
        return

    try:
        with st.spinner("Lendo documento..."):
            lido = _ler_docx(enviado.read())
    except Exception as erro:  # arquivo corrompido, formato inesperado
        st.error(f"Não consegui ler esse .docx: {erro}")
        return

    if not lido["campos"] and not lido["texto"]:
        st.error("Esse documento não tem dados de projeto reconhecíveis.")
        return

    st.session_state.projeto.update(lido["campos"])
    # Identificação só é sobrescrita onde ainda estava vazia.
    for campo, valor in lido["identificacao"].items():
        st.session_state.meta.setdefault(campo, valor)

    contexto = (
        "O usuário retornou com um documento DMAIC já existente.\n"
        f"Campos reconhecidos: "
        f"{json.dumps(lido['campos'], ensure_ascii=False)[:2500]}\n"
        f"Identificação: "
        f"{json.dumps(lido['identificacao'], ensure_ascii=False)[:500]}\n"
        f"Outros dados do documento: "
        f"{json.dumps(lido['avulsos'], ensure_ascii=False)[:1000]}\n"
        f"Texto do documento: {lido['texto'][:1500]}\n\n"
        "Faça um briefing em 3 parágrafos: (1) o que já foi construído, "
        "(2) o que ficou pendente, (3) o próximo passo mais importante. "
        "Depois conduza com UMA pergunta só."
    )

    mensagens = agent.montar_mensagens(
        chat=[{"role": "user",
               "content": "Retomei o projeto. Onde paramos?"}],
        projeto=st.session_state.projeto,
        etapa=st.session_state.etapa,
        ferramentas=st.session_state.ferramentas_usadas,
        aguardando=False,
        meta=st.session_state.meta,
        extra_ctx=contexto,
    )

    try:
        with st.spinner("Analisando o projeto retomado..."):
            resposta = agent.responder(state.credenciais(), mensagens)
    except LLMError as erro:
        st.error(str(erro))
        return

    sinais = agent.ler_sinais(resposta)
    st.session_state.chat = [{"role": "assistant", "content": sinais.texto}]
    st.session_state.pronto = True
    state.aplicar_sinais(sinais)
    state.autosave()
    st.rerun()


# ─────────────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────────────
def _render_status() -> None:
    if st.session_state.aguardando_campo:
        st.warning("**Aguardando retorno do campo**")
    else:
        st.caption(ETAPAS_META[st.session_state.etapa]["resumo"])

    st.markdown(_lista_etapas_html(), unsafe_allow_html=True)

    ferramentas = st.session_state.ferramentas_usadas
    if ferramentas:
        st.markdown("")
        _secao(f"Ferramentas aplicadas · {len(ferramentas)}")
        etiquetas = "".join(
            f'<span class="dmaic-tag">{escape(f)}</span>' for f in ferramentas
        )
        st.markdown(f'<div class="dmaic-tags">{etiquetas}</div>',
                    unsafe_allow_html=True)


def _lista_etapas_html() -> str:
    atual = indice_etapa(st.session_state.etapa)
    itens = []
    for i, etapa in enumerate(ETAPAS):
        meta = ETAPAS_META[etapa]
        if i < atual:
            estado, bolha = "feito", "✓"
        elif i == atual:
            estado, bolha = "atual", meta["letra"]
        else:
            estado, bolha = "adiante", meta["letra"]
        itens.append(
            f'<div class="dmaic-item {estado}">'
            f'<span class="dmaic-bolha">{bolha}</span>'
            f'{escape(meta["label"])}</div>'
        )
    return f'<div class="dmaic-lista">{"".join(itens)}</div>'


# ─────────────────────────────────────────────────────────────────
# EXPORTAÇÃO
# ─────────────────────────────────────────────────────────────────
def _gerar_documento(apurar: bool) -> bool:
    """Monta o .docx na sessão. Devolve se deu certo."""
    if apurar:
        try:
            dados = agent.extrair_dados(state.credenciais(),
                                        st.session_state.chat)
            quantos = state.atualizar_projeto(dados)
            st.caption(f"{quantos} campos apurados na conversa.")
        except LLMError as erro:
            st.warning(f"Não consegui apurar os dados: {erro}")

    try:
        st.session_state.word_bytes = gerar_word(
            projeto=st.session_state.projeto,
            meta=st.session_state.meta,
            chat=st.session_state.chat,
            etapa=st.session_state.etapa,
            ferramentas=st.session_state.ferramentas_usadas,
        )
    except Exception as erro:
        st.error(f"Falha ao montar o documento: {erro}")
        return False
    return True


def _render_export() -> None:
    if st.button("Gerar Word", use_container_width=True, type="primary",
                 disabled=not state.configurado()):
        with st.spinner("Montando o documento..."):
            if _gerar_documento(apurar=True):
                st.success("Documento pronto.")

    if not st.session_state.word_bytes:
        return

    if st.session_state.aguardando_campo:
        st.info("Documento de campo pronto — leve para o campo.")

    st.download_button(
        "Baixar .docx",
        data=st.session_state.word_bytes,
        file_name=nome_arquivo(st.session_state.projeto, st.session_state.meta),
        mime="application/vnd.openxmlformats-officedocument."
             "wordprocessingml.document",
        use_container_width=True,
    )
