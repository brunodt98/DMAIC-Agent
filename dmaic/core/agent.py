"""
core/agent.py — O consultor DMAIC: o que pedir ao modelo e como ler a resposta.

Nada aqui conhece Streamlit. As funções recebem o estado do projeto como
argumento e devolvem valores; guardar estado é tarefa de dmaic/state.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterator

from dmaic.core import llm
from dmaic.core.llm import LLMError
from dmaic.core.metodo import (
    CAMPOS_PROJETO,
    ETAPAS,
    FERRAMENTAS_KEYWORDS,
    indice_etapa,
    normalizar_ferramenta,
)
from dmaic.core.prompt import build_estado, montar_system_prompt

# Orçamento de histórico enviado ao modelo, em caracteres. Os modelos usados
# hoje têm 128k tokens ou mais de contexto; cortar em 12 mensagens de 1000
# caracteres fazia o consultor esquecer o problema que ele mesmo definiu.
ORCAMENTO_HISTORICO = 24_000

# Uma única mensagem gigante (um relatório colado, por exemplo) não pode
# consumir o orçamento inteiro.
LIMITE_POR_MENSAGEM = 6_000


@dataclass(frozen=True)
class Credenciais:
    """Quem chamar, com qual chave, em qual modelo."""

    provider: str
    api_key: str
    model: str

    def completas(self) -> bool:
        return bool(self.provider and self.api_key and self.model)


@dataclass
class Sinais:
    """O que a aplicação lê da resposta do consultor."""

    texto: str
    etapa: str | None = None
    ferramentas: list[str] = field(default_factory=list)
    aguardando_campo: bool = False


# ─────────────────────────────────────────────────────────────────
# MONTAGEM DAS MENSAGENS
# ─────────────────────────────────────────────────────────────────
def aparar_historico(chat: list[dict],
                     orcamento: int = ORCAMENTO_HISTORICO) -> list[dict]:
    """
    Mensagens mais recentes que couberem no orçamento, da mais antiga à mais
    nova.

    Mensagens inteiras entram ou ficam de fora; cortar uma mensagem no meio
    da frase é o que fazia o consultor perder o fio da conversa. A exceção é
    uma mensagem sozinha maior que o limite, que entra truncada.
    """
    selecionadas: list[dict] = []
    usado = 0

    for msg in reversed(chat):
        conteudo = msg.get("content") or ""
        if len(conteudo) > LIMITE_POR_MENSAGEM:
            conteudo = conteudo[:LIMITE_POR_MENSAGEM] + "\n[…trecho truncado]"
        if selecionadas and usado + len(conteudo) > orcamento:
            break
        selecionadas.append({"role": msg["role"], "content": conteudo})
        usado += len(conteudo)

    selecionadas.reverse()
    return selecionadas


def montar_mensagens(chat: list[dict], projeto: dict, etapa: str,
                     ferramentas: list[str], aguardando: bool,
                     meta: dict | None = None,
                     extra_ctx: str = "") -> list[dict]:
    """Conversa completa a enviar ao modelo: system prompt + histórico aparado."""
    estado = build_estado(
        projeto=projeto,
        etapa=etapa,
        ferramentas=ferramentas,
        aguardando=aguardando,
        meta=meta,
        extra_ctx=extra_ctx,
    )
    system = montar_system_prompt(estado)
    return [{"role": "system", "content": system}] + aparar_historico(chat)


# ─────────────────────────────────────────────────────────────────
# CHAMADAS AO MODELO
# ─────────────────────────────────────────────────────────────────
def responder_stream(creds: Credenciais,
                     mensagens: list[dict]) -> Iterator[str]:
    """Resposta do consultor em pedaços, para aparecer enquanto é escrita."""
    if not creds.completas():
        raise LLMError("Configure o provedor, a chave e o modelo na barra lateral.")
    return llm.chat_stream(
        creds.provider, creds.api_key, creds.model, mensagens,
        temperature=0.35, max_tokens=1800,
    )


def responder(creds: Credenciais, mensagens: list[dict]) -> str:
    """Resposta completa de uma vez — usada quando não há onde exibir o fluxo."""
    if not creds.completas():
        raise LLMError("Configure o provedor, a chave e o modelo na barra lateral.")
    return llm.chat(
        creds.provider, creds.api_key, creds.model, mensagens,
        temperature=0.35, max_tokens=1800,
    )


# ─────────────────────────────────────────────────────────────────
# LEITURA DO RODAPÉ DE CONTROLE
# ─────────────────────────────────────────────────────────────────
_RE_ETAPA = re.compile(r"\[\s*ETAPA\s*:\s*([A-Za-zÀ-ÿ]+)\s*\]", re.I)
_RE_FERRAMENTAS = re.compile(r"\[\s*FERRAMENTAS?\s*:\s*([^\]]*)\]", re.I)
_RE_AGUARDANDO = re.compile(
    r"\[\s*AGUARDANDO[_ ]CAMPO\s*:\s*(sim|s|n[ãa]o|n)\s*\]", re.I)
_RE_RODAPE = re.compile(
    r"\[\s*(?:ETAPA|FERRAMENTAS?|AGUARDANDO[_ ]CAMPO)\s*:[^\]]*\]\s*", re.I)


def ler_sinais(resposta: str) -> Sinais:
    """
    Separa o texto que o usuário vê dos marcadores de controle.

    Quando o modelo esquece o rodapé — acontece —, cai em heurísticas
    conservadoras em cima do texto da própria resposta.
    """
    etapa = _ler_etapa(resposta)
    ferramentas = _ler_ferramentas(resposta)
    aguardando = _ler_aguardando(resposta)
    texto = _RE_RODAPE.sub("", resposta).rstrip()

    return Sinais(
        texto=texto,
        etapa=etapa,
        ferramentas=ferramentas,
        aguardando_campo=aguardando,
    )


def _ler_etapa(resposta: str) -> str | None:
    achado = _RE_ETAPA.search(resposta)
    if achado:
        candidato = achado.group(1).strip().lower()
        if candidato in ETAPAS:
            return candidato
    return _etapa_heuristica(resposta)


# Frases de transição explícita. Deliberadamente estreitas: a palavra "medir"
# solta aparece em qualquer frase e fazia o app pular de etapa sozinho.
_FRASES_ETAPA = {
    "medir": ["etapa medir", "etapa de medir", "etapa m ", "m — medir",
              "iniciar a medição", "vamos medir agora"],
    "analisar": ["etapa analisar", "etapa de analisar", "etapa a ",
                 "a — analisar", "vamos analisar agora"],
    "melhorar": ["etapa melhorar", "etapa de melhorar", "etapa i ",
                 "i — melhorar", "vamos melhorar agora"],
    "controlar": ["etapa controlar", "etapa de controlar", "etapa c ",
                  "c — controlar", "vamos controlar agora"],
}


def _etapa_heuristica(resposta: str) -> str | None:
    baixo = resposta.lower()
    # Da última etapa para a primeira: se o texto anuncia CONTROLAR, é isso.
    for etapa in reversed(ETAPAS[1:]):
        if any(frase in baixo for frase in _FRASES_ETAPA[etapa]):
            return etapa
    return None


def _ler_ferramentas(resposta: str) -> list[str]:
    achado = _RE_FERRAMENTAS.search(resposta)
    if achado:
        declaradas = achado.group(1)
        if declaradas.strip().lower() in ("", "nenhuma", "none", "-"):
            return []
        nomes = (normalizar_ferramenta(n) for n in declaradas.split(","))
        return _sem_repetir(n for n in nomes if n)
    return _ferramentas_heuristica(resposta)


def _ferramentas_heuristica(resposta: str) -> list[str]:
    """
    Rede de segurança quando o rodapé falta. Só conta a ferramenta que aparece
    em contexto de aplicação, não de menção de passagem.
    """
    baixo = resposta.lower()
    achadas = []
    for canonico, palavras in FERRAMENTAS_KEYWORDS.items():
        if any(p in baixo for p in palavras):
            achadas.append(canonico)
    return achadas


def _ler_aguardando(resposta: str) -> bool:
    achado = _RE_AGUARDANDO.search(resposta)
    if achado:
        return achado.group(1).lower().startswith("s")
    return "plano de campo" in resposta.lower()


def _sem_repetir(itens) -> list[str]:
    vistos: list[str] = []
    for item in itens:
        if item not in vistos:
            vistos.append(item)
    return vistos


def proxima_etapa(atual: str, declarada: str | None) -> str:
    """
    Etapa resultante: o método DMAIC não volta atrás, e não pula etapas.

    Um salto de DEFINIR direto para CONTROLAR é sinal de alucinação, não de
    progresso — avança no máximo uma etapa por resposta.
    """
    if not declarada or declarada not in ETAPAS:
        return atual
    i_atual = indice_etapa(atual)
    i_nova = indice_etapa(declarada)
    if i_nova <= i_atual:
        return atual
    return ETAPAS[min(i_nova, i_atual + 1)]


# ─────────────────────────────────────────────────────────────────
# EXTRAÇÃO DE DADOS ESTRUTURADOS
# ─────────────────────────────────────────────────────────────────
_INSTRUCAO_EXTRACAO = (
    "Você extrai dados de projetos DMAIC de transcrições de consultoria.\n"
    "Responda SOMENTE com um objeto JSON.\n"
    "Inclua apenas campos que foram claramente respondidos na conversa — "
    "nunca invente, nunca preencha por dedução.\n"
    "Todos os valores devem ser strings em português.\n"
    "Campos permitidos: {campos}"
)


def extrair_dados(creds: Credenciais, chat: list[dict]) -> dict[str, str]:
    """
    Dados do projeto apurados na conversa.

    Devolve dicionário vazio quando não há nada novo ou quando a chamada
    falha — a extração é um acessório, não pode derrubar a sessão.
    """
    if not creds.completas() or not chat:
        return {}

    transcricao = "\n\n".join(
        f"{'CONSULTOR' if m['role'] == 'assistant' else 'USUÁRIO'}: {m['content']}"
        for m in aparar_historico(chat, orcamento=30_000)
    )
    mensagens = [
        {
            "role": "system",
            "content": _INSTRUCAO_EXTRACAO.format(campos=", ".join(CAMPOS_PROJETO)),
        },
        {"role": "user", "content": f"CONVERSA:\n{transcricao}"},
    ]

    try:
        bruto = llm.chat(
            creds.provider, creds.api_key, creds.model, mensagens,
            temperature=0, max_tokens=2000, json_mode=True,
        )
    except LLMError:
        # Nem todo modelo aceita response_format; tenta sem o modo JSON.
        try:
            bruto = llm.chat(
                creds.provider, creds.api_key, creds.model, mensagens,
                temperature=0, max_tokens=2000,
            )
        except LLMError:
            return {}

    return _limpar_extracao(bruto)


def _limpar_extracao(bruto: str) -> dict[str, str]:
    """Aceita só campos conhecidos, com valor textual não vazio."""
    dados = _json_solto(bruto)
    if not isinstance(dados, dict):
        return {}

    permitidos = set(CAMPOS_PROJETO)
    limpos: dict[str, str] = {}
    for chave, valor in dados.items():
        campo = str(chave).strip().lower()
        if campo not in permitidos:
            continue
        texto = _como_texto(valor)
        if texto:
            limpos[campo] = texto
    return limpos


def _json_solto(bruto: str) -> object:
    """JSON da resposta, mesmo quando vem embrulhado em texto ou em ```json."""
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        pass
    achado = re.search(r"\{.*\}", bruto, re.DOTALL)
    if not achado:
        return None
    try:
        return json.loads(achado.group())
    except json.JSONDecodeError:
        return None


def _como_texto(valor: object) -> str:
    """Achata lista e dicionário em texto — o modelo às vezes devolve assim."""
    if valor is None or isinstance(valor, bool):
        return ""
    if isinstance(valor, (list, tuple)):
        return "; ".join(t for t in (_como_texto(v) for v in valor) if t)
    if isinstance(valor, dict):
        return "; ".join(
            f"{k}: {t}" for k, v in valor.items() if (t := _como_texto(v))
        )
    return str(valor).strip()
