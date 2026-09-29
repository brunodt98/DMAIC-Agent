"""
core/metodo.py — O método DMAIC como dado: etapas, ferramentas, campos.

Só descrição do método. Nada de configuração de página nem de CSS, que são
assunto da interface (ver dmaic/ui/theme.py).
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────
# ETAPAS
# ─────────────────────────────────────────────────────────────────
ETAPAS = ["definir", "medir", "analisar", "melhorar", "controlar"]

ETAPAS_META = {
    "definir": {
        "letra": "D",
        "label": "Definir",
        "doc": "D — DEFINIR",
        "resumo": "Delimitar o problema, o impacto e o escopo",
    },
    "medir": {
        "letra": "M",
        "label": "Medir",
        "doc": "M — MEDIR",
        "resumo": "Quantificar a situação atual e estabelecer o baseline",
    },
    "analisar": {
        "letra": "A",
        "label": "Analisar",
        "doc": "A — ANALISAR",
        "resumo": "Encontrar e confirmar a causa raiz",
    },
    "melhorar": {
        "letra": "I",
        "label": "Melhorar",
        "doc": "I — MELHORAR",
        "resumo": "Escolher, planejar e testar a solução",
    },
    "controlar": {
        "letra": "C",
        "label": "Controlar",
        "doc": "C — CONTROLAR",
        "resumo": "Sustentar o ganho e padronizar o processo",
    },
}


def indice_etapa(etapa: str) -> int:
    """Posição da etapa na sequência, ou 0 quando o nome não é reconhecido."""
    try:
        return ETAPAS.index(etapa)
    except ValueError:
        return 0


# ─────────────────────────────────────────────────────────────────
# ROADMAP DE PRÓXIMOS PASSOS (por etapa) — usado no documento Word
# ─────────────────────────────────────────────────────────────────
ROADMAP = {
    "definir": [
        "Aplicar Funil de Problemas para refinar o escopo com os dados coletados",
        "Validar o problema com dados mensuráveis — início da etapa MEDIR",
        "Mapear o processo atual (SIPOC) com a equipe",
        "Confirmar VOC — Voz do Cliente e traduzir em CTQ",
        "Aprovar Project Charter com o patrocinador",
    ],
    "medir": [
        "Analisar os dados coletados e calcular baseline definitivo",
        "Estratificar os dados por causa, turno, operador e frequência",
        "Construir gráfico de Pareto para priorizar causas",
        "Validar sistema de medição (MSA) se necessário",
        "Iniciar transição para a etapa ANALISAR",
    ],
    "analisar": [
        "Conduzir Diagrama de Ishikawa completo pelas 6 categorias",
        "Aplicar 5 Porquês para aprofundar na causa mais provável",
        "Construir Matriz de Priorização de Causas",
        "Confirmar causa raiz com evidências quantitativas",
        "Propor soluções baseadas na causa raiz confirmada",
    ],
    "melhorar": [
        "Avaliar soluções com Matriz Esforço × Impacto",
        "Aplicar FMEA para antecipar riscos das soluções",
        "Estruturar Plano de Ação (5W2H) para a solução escolhida",
        "Executar plano piloto e medir resultado",
        "Ajustar plano de ação se necessário",
    ],
    "controlar": [
        "Definir Gráfico de Controle (CEP) para monitoramento contínuo",
        "Elaborar Plano de Controle formal",
        "Padronizar novo processo em SOP",
        "Treinar equipe no novo padrão",
        "Registrar Lições Aprendidas e apresentar fechamento ao patrocinador",
    ],
}


# ─────────────────────────────────────────────────────────────────
# FERRAMENTAS DMAIC
# ─────────────────────────────────────────────────────────────────
# Nomes canônicos, na ordem em que aparecem no método. O consultor declara
# quais aplicou; estas palavras-chave servem de rede de segurança quando a
# declaração vem ausente ou escrita de outro jeito.
FERRAMENTAS_KEYWORDS = {
    "Funil de Problemas":    ["funil de problemas", "funil do problema"],
    "SIPOC":                 ["sipoc"],
    "VOC":                   ["voz do cliente", "voc"],
    "CTQ":                   ["ctq", "critical to quality"],
    "Project Charter":       ["project charter", "charter"],
    "Mapa de Processo":      ["mapa de processo", "fluxo do processo"],
    "Plano de Coleta":       ["plano de coleta"],
    "Pareto":                ["pareto"],
    "Ishikawa":              ["ishikawa", "causa e efeito", "espinha de peixe"],
    "5 Porquês":             ["5 porquês", "cinco porquês", "5 por quês"],
    "Matriz de Priorização": ["matriz de priorização", "priorização de causas"],
    "FMEA":                  ["fmea"],
    "5W2H":                  ["5w2h"],
    "Gráfico de Controle":   ["gráfico de controle", "cep"],
    "SOP":                   ["sop", "procedimento operacional"],
}

FERRAMENTAS = list(FERRAMENTAS_KEYWORDS)


def normalizar_ferramenta(nome: str) -> str | None:
    """
    Converte o nome que o consultor escreveu no nome canônico da ferramenta.
    Devolve None quando não reconhece — melhor ignorar que registrar lixo.
    """
    alvo = nome.strip().lower()
    if not alvo:
        return None
    for canonico, palavras in FERRAMENTAS_KEYWORDS.items():
        if alvo == canonico.lower() or alvo in palavras:
            return canonico
    for canonico, palavras in FERRAMENTAS_KEYWORDS.items():
        if any(p in alvo for p in palavras):
            return canonico
    return None


# ─────────────────────────────────────────────────────────────────
# CAMPOS EXTRAÍDOS DA CONVERSA — usados pelo extrator de dados
# ─────────────────────────────────────────────────────────────────
CAMPOS_PROJETO = [
    "titulo", "empresa", "responsavel", "problema", "impacto", "objetivo",
    "escopo", "equipe", "prazo", "situacao_atual", "meta", "dados",
    "frequencia", "baseline",
    "sipoc_fornecedores", "sipoc_entradas", "sipoc_processo",
    "sipoc_saidas", "sipoc_clientes",
    "voc", "ctq",
    "causas", "causa_raiz", "evidencias", "cinco_porques",
    "ishikawa_metodo", "ishikawa_maquina", "ishikawa_mao_obra",
    "ishikawa_material", "ishikawa_meio_ambiente", "ishikawa_medicao",
    "matriz_priorizacao",
    "solucoes", "solucao_escolhida", "fmea", "plano_acao_5w2h",
    "recursos", "riscos", "resultados", "monitoramento",
    "indicadores", "padronizacao", "licoes",
]

# Rótulos legíveis, usados no documento e na tela de revisão dos dados.
CAMPOS_LABELS = {
    "titulo":                 "Título do projeto",
    "problema":               "Problema identificado",
    "impacto":                "Impacto",
    "objetivo":               "Objetivo do projeto",
    "escopo":                 "Escopo",
    "equipe":                 "Equipe envolvida",
    "prazo":                  "Prazo",
    "situacao_atual":         "Situação atual (dados)",
    "meta":                   "Meta quantitativa",
    "dados":                  "Dados disponíveis",
    "frequencia":             "Frequência",
    "baseline":               "Baseline",
    "sipoc_fornecedores":     "Fornecedores (S)",
    "sipoc_entradas":         "Entradas (I)",
    "sipoc_processo":         "Processo (P)",
    "sipoc_saidas":           "Saídas (O)",
    "sipoc_clientes":         "Clientes (C)",
    "voc":                    "VOC — Voz do Cliente",
    "ctq":                    "CTQ",
    "causas":                 "Possíveis causas",
    "causa_raiz":             "Hipótese de causa raiz",
    "evidencias":             "Evidências disponíveis",
    "cinco_porques":          "5 Porquês",
    "matriz_priorizacao":     "Matriz de Priorização",
    "ishikawa_metodo":        "Método",
    "ishikawa_maquina":       "Máquina",
    "ishikawa_mao_obra":      "Mão de Obra",
    "ishikawa_material":      "Material",
    "ishikawa_meio_ambiente": "Meio Ambiente",
    "ishikawa_medicao":       "Medição",
    "solucoes":               "Soluções propostas",
    "solucao_escolhida":      "Solução escolhida",
    "fmea":                   "FMEA",
    "plano_acao_5w2h":        "Plano de Ação (5W2H)",
    "recursos":               "Recursos necessários",
    "riscos":                 "Riscos identificados",
    "resultados":             "Resultados esperados",
    "monitoramento":          "Monitoramento",
    "indicadores":            "KPIs de monitoramento",
    "padronizacao":           "Padronização (SOP)",
    "licoes":                 "Lições aprendidas",
}


def label_campo(campo: str) -> str:
    """Rótulo legível de um campo; cai no próprio nome quando não há rótulo."""
    return CAMPOS_LABELS.get(campo, campo.replace("_", " ").capitalize())


# Identificação do projeto: vive em `meta`, não em `projeto`, porque é
# cadastro e não achado da conversa.
CAMPOS_META_LABELS = {
    "empresa":      "Empresa",
    "responsavel":  "Responsável",
    "patrocinador": "Patrocinador",
    "area":         "Área",
    "numero":       "Nº Projeto",
    "inicio":       "Início",
}

_LABELS_INVERTIDO = {
    label.lower(): campo for campo, label in CAMPOS_LABELS.items()
}

_LABELS_META_INVERTIDO = {
    label.lower(): campo for campo, label in CAMPOS_META_LABELS.items()
}


def campo_meta_por_label(label: str) -> str | None:
    """Campo de identificação a partir do rótulo usado no documento."""
    alvo = " ".join((label or "").split()).strip().lower().rstrip(":")
    return _LABELS_META_INVERTIDO.get(alvo)


def campo_por_label(label: str) -> str | None:
    """
    Nome do campo a partir do rótulo — o caminho de volta ao ler um .docx que a
    própria ferramenta gerou.

    Sem isso, retomar um projeto gravava chaves como "Problema identificado" no
    lugar de "problema", e o documento seguinte saía vazio.
    """
    alvo = " ".join((label or "").split()).strip().lower().rstrip(":")
    if not alvo:
        return None
    if alvo in _LABELS_INVERTIDO:
        return _LABELS_INVERTIDO[alvo]
    # "VOC — Voz do Cliente" pode voltar do Word só como "VOC".
    for rotulo, campo in _LABELS_INVERTIDO.items():
        if alvo == rotulo.split("—")[0].strip():
            return campo
    if alvo.replace(" ", "_") in CAMPOS_PROJETO:
        return alvo.replace(" ", "_")
    return None
