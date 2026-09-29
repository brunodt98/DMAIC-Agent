"""
core/snapshot.py — O projeto como arquivo: salvar, abrir e guardar sozinho.

Duas formas de persistência, com propósitos diferentes:

- arquivo de projeto (.dmaic.json): o usuário baixa e guarda onde quiser.
  Portátil, serve de backup e atravessa máquinas.
- autosave: uma cópia gravada em disco a cada resposta, para um F5 não
  apagar a sessão. Só faz sentido quando a aplicação roda na máquina do
  próprio usuário (ver dmaic/ui/sidebar.py).

Um arquivo aberto aqui vem de fora, então nada é aproveitado sem passar pela
validação: etapa tem que existir no método, mensagem tem que ter papel
conhecido, valor tem que ser texto.
"""

from __future__ import annotations

import datetime
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from dmaic.core.metodo import CAMPOS_PROJETO, ETAPAS, normalizar_ferramenta

# Versão do formato. Muda quando a estrutura do arquivo mudar de forma que um
# arquivo antigo não possa mais ser lido do mesmo jeito.
FORMATO = 1

NOME_AUTOSAVE = "sessao_atual.json"
EXTENSAO = ".dmaic.json"

_PAPEIS = ("user", "assistant")
_CAMPOS_META = ("empresa", "responsavel", "patrocinador", "area",
                "numero", "inicio")

# Um arquivo maior que isso não é um projeto DMAIC.
LIMITE_BYTES = 8 * 1024 * 1024


class SnapshotInvalido(Exception):
    """Arquivo que não é um projeto DMAIC legível."""


@dataclass
class Snapshot:
    """Estado completo de um projeto, pronto para virar arquivo e voltar."""

    projeto: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)
    chat: list = field(default_factory=list)
    etapa: str = "definir"
    ferramentas: list = field(default_factory=list)
    aguardando_campo: bool = False
    salvo_em: str = ""

    def vazio(self) -> bool:
        return not self.chat and not self.projeto and not self.meta

    def descricao(self) -> str:
        """Uma linha para identificar o projeto na interface."""
        titulo = (self.projeto.get("titulo")
                  or self.projeto.get("problema")
                  or self.meta.get("empresa")
                  or "Projeto sem título")
        return str(titulo)[:70]


# ─────────────────────────────────────────────────────────────────
# SERIALIZAÇÃO
# ─────────────────────────────────────────────────────────────────
def para_bytes(snap: Snapshot) -> bytes:
    """Arquivo de projeto, pronto para download."""
    dados = {
        "formato": FORMATO,
        "app": "dmaic-agent",
        "salvo_em": snap.salvo_em or _agora(),
        "etapa": snap.etapa,
        "aguardando_campo": bool(snap.aguardando_campo),
        "ferramentas": list(snap.ferramentas),
        "meta": dict(snap.meta),
        "projeto": dict(snap.projeto),
        "chat": [
            {"role": m["role"], "content": m["content"]}
            for m in snap.chat
        ],
    }
    return json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")


def de_bytes(bruto: bytes) -> Snapshot:
    """
    Snapshot validado a partir do conteúdo de um arquivo.

    Levanta SnapshotInvalido com uma frase que o usuário entende — o arquivo
    pode ser de outro app, de uma versão futura ou simplesmente corrompido.
    """
    if not bruto:
        raise SnapshotInvalido("O arquivo está vazio.")
    if len(bruto) > LIMITE_BYTES:
        raise SnapshotInvalido("O arquivo é grande demais para ser um projeto.")

    try:
        dados = json.loads(bruto.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise SnapshotInvalido("O arquivo não está em texto UTF-8.") from e
    except json.JSONDecodeError as e:
        raise SnapshotInvalido(f"O arquivo não é um JSON válido: {e.msg}.") from e

    if not isinstance(dados, dict):
        raise SnapshotInvalido("O conteúdo do arquivo não é um projeto.")

    formato = dados.get("formato")
    if formato is None:
        raise SnapshotInvalido(
            "Esse arquivo não foi salvo pelo DMAIC Agent.")
    if not isinstance(formato, int) or formato > FORMATO:
        raise SnapshotInvalido(
            f"Arquivo salvo por uma versão mais nova (formato {formato}). "
            f"Atualize a aplicação para abri-lo."
        )

    return Snapshot(
        projeto=_limpar_dict(dados.get("projeto"), permitidos=CAMPOS_PROJETO),
        meta=_limpar_dict(dados.get("meta"), permitidos=_CAMPOS_META),
        chat=_limpar_chat(dados.get("chat")),
        etapa=_limpar_etapa(dados.get("etapa")),
        ferramentas=_limpar_ferramentas(dados.get("ferramentas")),
        aguardando_campo=bool(dados.get("aguardando_campo")),
        salvo_em=str(dados.get("salvo_em") or ""),
    )


def _limpar_dict(valor: object, permitidos: list | tuple) -> dict:
    if not isinstance(valor, dict):
        return {}
    aceitos = set(permitidos)
    return {
        str(k): str(v).strip()
        for k, v in valor.items()
        if str(k) in aceitos and isinstance(v, (str, int, float))
        and str(v).strip()
    }


def _limpar_chat(valor: object) -> list[dict]:
    if not isinstance(valor, list):
        return []
    mensagens = []
    for item in valor:
        if not isinstance(item, dict):
            continue
        papel = item.get("role")
        texto = item.get("content")
        if papel in _PAPEIS and isinstance(texto, str) and texto.strip():
            mensagens.append({"role": papel, "content": texto})
    return mensagens


def _limpar_etapa(valor: object) -> str:
    return valor if valor in ETAPAS else "definir"


def _limpar_ferramentas(valor: object) -> list[str]:
    if not isinstance(valor, list):
        return []
    limpas: list[str] = []
    for item in valor:
        if not isinstance(item, str):
            continue
        canonico = normalizar_ferramenta(item)
        if canonico and canonico not in limpas:
            limpas.append(canonico)
    return limpas


def nome_arquivo(snap: Snapshot) -> str:
    """Nome sugerido para o download do projeto."""
    import re

    base = snap.descricao()
    limpo = re.sub(r"[^\w\s-]", "", base, flags=re.UNICODE).strip()
    limpo = re.sub(r"\s+", "_", limpo)[:40] or "projeto"
    return f"{limpo}{EXTENSAO}"


def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────────
# AUTOSAVE EM DISCO
# ─────────────────────────────────────────────────────────────────
def diretorio_dados() -> Path:
    """
    Onde o autosave mora. Fora do repositório, para projeto de cliente nunca
    acabar num commit.
    """
    configurado = os.environ.get("DMAIC_DATA_DIR")
    if configurado:
        return Path(configurado).expanduser()
    return Path.home() / ".dmaic_agent"


def caminho_autosave() -> Path:
    return diretorio_dados() / NOME_AUTOSAVE


def gravar_autosave(snap: Snapshot) -> Path | None:
    """
    Grava a sessão em disco. Devolve o caminho, ou None quando não foi
    possível gravar — autosave é conveniência e não pode derrubar a conversa.

    A gravação é atômica: escreve num temporário e substitui. Sem isso, um F5
    no meio da escrita deixaria para trás um arquivo pela metade, e a sessão
    seguinte não conseguiria abrir justamente o que deveria salvá-la.
    """
    if snap.vazio():
        return None

    snap.salvo_em = _agora()
    destino = caminho_autosave()
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destino.parent, prefix=".tmp_", delete=False
        ) as tmp:
            tmp.write(para_bytes(snap))
            temporario = Path(tmp.name)
        temporario.replace(destino)
        return destino
    except OSError:
        return None


def ler_autosave() -> Snapshot | None:
    """Sessão gravada, ou None quando não existe ou não dá para ler."""
    origem = caminho_autosave()
    try:
        bruto = origem.read_bytes()
    except OSError:
        return None
    try:
        snap = de_bytes(bruto)
    except SnapshotInvalido:
        return None
    return None if snap.vazio() else snap


def apagar_autosave() -> None:
    """Remove a sessão gravada — usado ao começar um projeto novo."""
    try:
        caminho_autosave().unlink(missing_ok=True)
    except OSError:
        pass
