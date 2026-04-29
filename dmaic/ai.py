"""
ai.py — Todas as chamadas à API Groq ficam aqui.

Responsabilidades:
- Chamada principal do consultor (ai_chat)
- Extração estruturada de dados da conversa (extrair_dados)
- Detecção de ferramentas usadas numa resposta (detectar_ferramentas)
- Detecção de etapa com base nas mensagens recentes (detectar_etapa)
"""

import json
import re

import streamlit as st
from groq import Groq

from dmaic.config import ETAPAS, FERRAMENTAS_KEYWORDS, CAMPOS_PROJETO
from dmaic.prompt import CONSULTOR_SYSTEM_PROMPT, build_estado


# ─────────────────────────────────────────────────────────────────
# CLIENTE GROQ
# ─────────────────────────────────────────────────────────────────
def _get_client() -> Groq | None:
    key = st.session_state.get("groq_key", "")
    if not key:
        return None
    return Groq(api_key=key)


def _handle_error(err: Exception) -> str:
    msg = str(err)
    if "401" in msg:
        return "⚠️ API Key inválida. Verifique na barra lateral."
    if "429" in msg:
        return "⚠️ Limite de requisições atingido. Aguarde alguns segundos."
    if "413" in msg:
        return "⚠️ Conversa longa demais. Exporte o documento e recarregue a página."
    return f"⚠️ Erro inesperado: {msg[:140]}"


# ─────────────────────────────────────────────────────────────────
# CHAMADA PRINCIPAL — consultor DMAIC
# ─────────────────────────────────────────────────────────────────
def ai_chat(extra_ctx: str = "") -> str:
    """Envia o histórico ao consultor e retorna a resposta."""
    client = _get_client()
    if not client:
        return "⚠️ Configure sua API Key na barra lateral."

    estado = build_estado(
        projeto=st.session_state.projeto,
        etapa=st.session_state.etapa,
        ferramentas=st.session_state.get("ferramentas_usadas", []),
        aguardando=st.session_state.get("aguardando_campo", False),
        extra_ctx=extra_ctx,
    )
    system = CONSULTOR_SYSTEM_PROMPT.format(estado=estado)

    # Últimas 12 mensagens, truncadas para caber no contexto
    historico = []
    for m in st.session_state.chat[-12:]:
        txt = m["content"]
        if len(txt) > 1000:
            txt = txt[:1000] + "…"
        historico.append({"role": m["role"], "content": txt})

    msgs = [{"role": "system", "content": system}] + historico

    try:
        r = client.chat.completions.create(
            messages=msgs,
            model=st.session_state.get("model", "llama-3.3-70b-versatile"),
            temperature=0.35,
            max_tokens=1400,
        )
        return r.choices[0].message.content
    except Exception as e:
        return _handle_error(e)


# ─────────────────────────────────────────────────────────────────
# EXTRAÇÃO DE DADOS ESTRUTURADOS
# ─────────────────────────────────────────────────────────────────
def extrair_dados(chat: list) -> dict:
    """
    Pede ao modelo que extraia dados estruturados da conversa
    e retorna um dict com os campos preenchidos.
    """
    client = _get_client()
    if not client:
        return {}

    conversa = "\n".join(
        f"{m['role'].upper()}: {m['content'][:500]}"
        for m in chat[-30:]
    )
    campos_str = ", ".join(CAMPOS_PROJETO)

    prompt = (
        f"Extraia os dados do projeto DMAIC da conversa abaixo.\n"
        f"Retorne SOMENTE um JSON com os campos que foram claramente respondidos.\n"
        f"Campos possíveis: {campos_str}.\n"
        f"Ignore campos não mencionados. Valores devem ser strings.\n"
        f"Retorne apenas o JSON, sem explicações.\n\n"
        f"CONVERSA:\n{conversa}"
    )

    try:
        r = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=st.session_state.get("model", "llama-3.3-70b-versatile"),
            temperature=0,
            max_tokens=1000,
        )
        raw = r.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────────────────────────
# DETECÇÃO DE FERRAMENTAS
# ─────────────────────────────────────────────────────────────────
def detectar_ferramentas(texto: str) -> list[str]:
    """Detecta quais ferramentas foram aplicadas em uma resposta do agente."""
    t = texto.lower()
    return [
        ferramenta
        for ferramenta, palavras in FERRAMENTAS_KEYWORDS.items()
        if any(p in t for p in palavras)
    ]


# ─────────────────────────────────────────────────────────────────
# DETECÇÃO DE ETAPA
# ─────────────────────────────────────────────────────────────────
def detectar_etapa(chat: list) -> str:
    """
    Detecta a etapa atual com base nas últimas mensagens.
    Só avança, nunca retrocede.
    """
    conversa = " ".join(m["content"] for m in chat[-8:]).lower()
    atual    = st.session_state.etapa
    atual_i  = ETAPAS.index(atual)

    mapa = {
        "controlar": ["controlar", "controle", "c —", "etapa c"],
        "melhorar":  ["melhorar", "i —", "etapa i", "melhoria"],
        "analisar":  ["analisar", "análise", "a —", "etapa a"],
        "medir":     ["medir", "medição", "m —", "etapa m"],
    }
    for etapa, palavras in mapa.items():
        if any(p in conversa for p in palavras):
            novo_i = ETAPAS.index(etapa)
            if novo_i >= atual_i:
                return etapa
    return atual
