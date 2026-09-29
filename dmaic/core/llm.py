"""
llm.py — Camada única de acesso aos provedores de LLM.

Groq e OpenRouter falam o mesmo dialeto (API compatível com OpenAI), então um
cliente HTTP atende os dois e o SDK específico de provedor deixa de ser
necessário.

A lista de modelos é buscada no próprio provedor em tempo de execução. Uma
lista fixa no código envelhece: o modelo sai do ar, o usuário seleciona e
recebe um 404 sem explicação.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator

import httpx

# Gerar a resposta inteira leva dezenas de segundos; abrir a conexão, não.
TIMEOUT_STREAM = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)
TIMEOUT_CURTO = httpx.Timeout(20.0)


class LLMError(Exception):
    """Erro já traduzido para uma frase que o usuário entende."""


# ─────────────────────────────────────────────────────────────────
# PROVEDORES
# ─────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    base_url: str
    keys_url: str
    key_prefix: str
    # Ordem de preferência para escolher o modelo padrão. Só é usada quando o
    # id aparece na lista que o provedor devolveu, então um id que saia do ar
    # apenas deixa de ser escolhido.
    preferidos: tuple[str, ...]


PROVIDERS: dict[str, Provider] = {
    "groq": Provider(
        id="groq",
        label="Groq",
        base_url="https://api.groq.com/openai/v1",
        keys_url="https://console.groq.com/keys",
        key_prefix="gsk_",
        preferidos=(
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-120b",
            "moonshotai/kimi-k2-instruct",
            "deepseek-r1-distill-llama-70b",
        ),
    ),
    "openrouter": Provider(
        id="openrouter",
        label="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        keys_url="https://openrouter.ai/settings/keys",
        key_prefix="sk-or-",
        preferidos=(
            "deepseek/deepseek-chat-v3.1:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.0-flash-001",
        ),
    ),
}

PROVIDER_PADRAO = "groq"


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    contexto: int | None
    gratuito: bool

    def descricao(self) -> str:
        """Texto curto para o selectbox da sidebar."""
        partes = [self.label]
        if self.contexto:
            partes.append(f"{self.contexto // 1000}k")
        if self.gratuito:
            partes.append("grátis")
        return partes[0] + (f"  ·  {' · '.join(partes[1:])}" if partes[1:] else "")


# Modelos que não servem para conversar: áudio, imagem, embeddings, moderação.
_IDS_IGNORADOS = (
    "whisper", "tts", "embed", "guard", "moderation", "rerank",
    "sdxl", "flux", "stable-diffusion", "dall-e", "playai",
)


def _e_conversacional(model_id: str) -> bool:
    baixo = model_id.lower()
    return not any(termo in baixo for termo in _IDS_IGNORADOS)


# ─────────────────────────────────────────────────────────────────
# ERROS
# ─────────────────────────────────────────────────────────────────
def _traduzir_http(status: int, corpo: str, prov: Provider) -> LLMError:
    if status in (401, 403):
        return LLMError(
            f"Chave da {prov.label} inválida ou sem permissão. "
            f"Confira em {prov.keys_url}."
        )
    if status == 402:
        return LLMError(
            f"Sua conta {prov.label} está sem crédito para este modelo. "
            f"Escolha um modelo gratuito na barra lateral."
        )
    if status == 404:
        return LLMError(
            "Este modelo não está mais disponível no provedor. "
            "Selecione outro na barra lateral."
        )
    if status == 413:
        return LLMError(
            "A conversa ficou longa demais para este modelo. "
            "Exporte o documento e comece uma nova sessão a partir dele."
        )
    if status == 429:
        return LLMError(
            "Limite de requisições do provedor atingido. "
            "Aguarde alguns segundos e tente de novo."
        )
    if status >= 500:
        return LLMError(
            f"O provedor {prov.label} está instável agora (erro {status}). "
            f"Tente novamente em instantes."
        )

    detalhe = corpo.strip()
    try:  # provedores compatíveis com OpenAI devolvem {"error": {"message": ...}}
        detalhe = json.loads(corpo)["error"]["message"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return LLMError(f"Erro {status} do provedor: {detalhe[:200]}")


def _traduzir_rede(err: Exception) -> LLMError:
    if isinstance(err, httpx.ReadTimeout):
        return LLMError(
            "O modelo demorou demais para responder. "
            "Tente novamente ou escolha um modelo mais rápido."
        )
    if isinstance(err, httpx.ConnectError):
        return LLMError("Sem conexão com o provedor. Verifique sua internet.")
    return LLMError(f"Falha de comunicação com o provedor: {str(err)[:160]}")


# ─────────────────────────────────────────────────────────────────
# INFRA HTTP
# ─────────────────────────────────────────────────────────────────
def _provider(provider_id: str) -> Provider:
    prov = PROVIDERS.get(provider_id)
    if prov is None:
        raise LLMError(f"Provedor desconhecido: {provider_id}")
    return prov


def _headers(prov: Provider, api_key: str) -> dict[str, str]:
    cab = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if prov.id == "openrouter":
        # A OpenRouter usa estes campos para identificar o app nos rankings.
        cab["HTTP-Referer"] = "https://github.com/brunodt98/dmaic-agent"
        cab["X-Title"] = "DMAIC Agent"
    return cab


# ─────────────────────────────────────────────────────────────────
# LISTA DE MODELOS
# ─────────────────────────────────────────────────────────────────
def listar_modelos(provider_id: str, api_key: str) -> list[Model]:
    """
    Modelos de chat disponíveis no provedor, do mais relevante ao menos.

    O resultado fica em cache por (provedor, chave) para não repetir a
    chamada em cada rerun do Streamlit.
    """
    if not api_key:
        return []
    return list(_listar_modelos_cache(provider_id, api_key))


@lru_cache(maxsize=8)
def _listar_modelos_cache(provider_id: str, api_key: str) -> tuple[Model, ...]:
    prov = _provider(provider_id)
    try:
        r = httpx.get(
            f"{prov.base_url}/models",
            headers=_headers(prov, api_key),
            timeout=TIMEOUT_CURTO,
        )
    except httpx.HTTPError as e:
        raise _traduzir_rede(e) from e

    if r.status_code >= 400:
        raise _traduzir_http(r.status_code, r.text, prov)

    try:
        bruto = r.json().get("data", [])
    except json.JSONDecodeError as e:
        raise LLMError("O provedor devolveu uma resposta ilegível.") from e

    modelos = [m for m in (_parse_modelo(item) for item in bruto) if m]
    return tuple(_ordenar(modelos, prov))


def _parse_modelo(item: dict) -> Model | None:
    model_id = item.get("id")
    if not model_id or not _e_conversacional(model_id):
        return None
    if item.get("active") is False:  # a Groq marca modelos desativados
        return None

    # A Groq chama de context_window; a OpenRouter, de context_length.
    contexto = item.get("context_window") or item.get("context_length")

    # A OpenRouter informa preço por token como string; "0" significa grátis.
    preco = item.get("pricing") or {}
    try:
        gratuito = float(preco.get("prompt", 1)) == 0 and bool(preco)
    except (TypeError, ValueError):
        gratuito = False

    return Model(
        id=model_id,
        label=item.get("name") or model_id,
        contexto=int(contexto) if isinstance(contexto, (int, float)) else None,
        gratuito=gratuito or model_id.endswith(":free"),
    )


def _ordenar(modelos: list[Model], prov: Provider) -> list[Model]:
    """Preferidos primeiro, na ordem declarada; o resto por contexto."""
    posicao = {mid: i for i, mid in enumerate(prov.preferidos)}
    return sorted(
        modelos,
        key=lambda m: (
            posicao.get(m.id, len(posicao)),
            -(m.contexto or 0),
            m.id,
        ),
    )


def modelo_padrao(modelos: list[Model]) -> str:
    """Primeiro modelo da lista já ordenada — vazio se o provedor não devolveu nada."""
    return modelos[0].id if modelos else ""


def validar_chave(provider_id: str, api_key: str) -> list[Model]:
    """
    Confirma que a chave funciona devolvendo os modelos que ela alcança.
    Levanta LLMError com a razão quando não funciona.
    """
    modelos = listar_modelos(provider_id, api_key)
    if not modelos:
        raise LLMError(
            "A chave foi aceita, mas nenhum modelo de conversa está "
            "disponível nela."
        )
    return modelos


def limpar_cache_modelos() -> None:
    """Descarta o cache de modelos — usado ao trocar de chave ou provedor."""
    _listar_modelos_cache.cache_clear()


# ─────────────────────────────────────────────────────────────────
# CHAMADAS DE CHAT
# ─────────────────────────────────────────────────────────────────
def _payload(model: str, mensagens: list[dict], temperature: float,
             max_tokens: int, stream: bool, json_mode: bool) -> dict:
    corpo: dict = {
        "model": model,
        "messages": mensagens,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if json_mode:
        corpo["response_format"] = {"type": "json_object"}
    return corpo


def chat_stream(provider_id: str, api_key: str, model: str,
                mensagens: list[dict], temperature: float = 0.35,
                max_tokens: int = 1800) -> Iterator[str]:
    """
    Gera a resposta em pedaços, para o texto aparecer enquanto é escrito.

    Levanta LLMError antes do primeiro pedaço quando a requisição falha; uma
    falha no meio do fluxo encerra o gerador com o que já foi entregue.
    """
    prov = _provider(provider_id)
    corpo = _payload(model, mensagens, temperature, max_tokens,
                     stream=True, json_mode=False)

    try:
        with httpx.Client(timeout=TIMEOUT_STREAM) as client:
            with client.stream(
                "POST",
                f"{prov.base_url}/chat/completions",
                headers=_headers(prov, api_key),
                json=corpo,
            ) as r:
                if r.status_code >= 400:
                    r.read()
                    raise _traduzir_http(r.status_code, r.text, prov)

                for linha in r.iter_lines():
                    # A OpenRouter intercala comentários SSE (": PROCESSING")
                    # para manter a conexão viva; só "data:" interessa.
                    if not linha.startswith("data:"):
                        continue
                    dado = linha[len("data:"):].strip()
                    if dado == "[DONE]":
                        return
                    pedaco = _extrair_delta(dado)
                    if pedaco:
                        yield pedaco
    except httpx.HTTPError as e:
        raise _traduzir_rede(e) from e


def _extrair_delta(dado: str) -> str:
    """Conteúdo de um evento SSE; string vazia para eventos sem texto."""
    try:
        escolhas = json.loads(dado).get("choices") or []
        return (escolhas[0].get("delta") or {}).get("content") or ""
    except (json.JSONDecodeError, AttributeError, IndexError, KeyError):
        return ""


def chat(provider_id: str, api_key: str, model: str, mensagens: list[dict],
         temperature: float = 0.35, max_tokens: int = 1800,
         json_mode: bool = False) -> str:
    """Resposta completa de uma vez — para tarefas internas, sem streaming."""
    prov = _provider(provider_id)
    corpo = _payload(model, mensagens, temperature, max_tokens,
                     stream=False, json_mode=json_mode)

    try:
        r = httpx.post(
            f"{prov.base_url}/chat/completions",
            headers=_headers(prov, api_key),
            json=corpo,
            timeout=TIMEOUT_STREAM,
        )
    except httpx.HTTPError as e:
        raise _traduzir_rede(e) from e

    if r.status_code >= 400:
        raise _traduzir_http(r.status_code, r.text, prov)

    try:
        return r.json()["choices"][0]["message"]["content"] or ""
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise LLMError("O provedor devolveu uma resposta em formato inesperado.") from e
