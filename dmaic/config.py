"""
config.py — Constantes globais, configuração da página e CSS.
"""

# ─────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ─────────────────────────────────────────────────────────────────
PAGE_CONFIG = dict(
    page_title="DMAIC Agent",
    page_icon="🎯",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
.stApp { background: #0f1117; }
section[data-testid="stSidebar"] { background: #111827; }
.stChatMessage { background: #1a2035; border-radius: 10px; margin-bottom: 4px; }
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 3px solid #2E86C1;
}
</style>
"""

# ─────────────────────────────────────────────────────────────────
# MODELOS GROQ DISPONÍVEIS
# ─────────────────────────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
]

# ─────────────────────────────────────────────────────────────────
# ETAPAS DMAIC
# ─────────────────────────────────────────────────────────────────
ETAPAS = ["definir", "medir", "analisar", "melhorar", "controlar"]

ETAPAS_META = {
    "definir":   {"emoji": "🎯", "label": "Definir",   "doc": "D — DEFINIR"},
    "medir":     {"emoji": "📏", "label": "Medir",     "doc": "M — MEDIR"},
    "analisar":  {"emoji": "🔍", "label": "Analisar",  "doc": "A — ANALISAR"},
    "melhorar":  {"emoji": "🚀", "label": "Melhorar",  "doc": "I — MELHORAR"},
    "controlar": {"emoji": "📊", "label": "Controlar", "doc": "C — CONTROLAR"},
}

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
# FERRAMENTAS DMAIC — mapeamento para detecção automática
# ─────────────────────────────────────────────────────────────────
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
    "indicadores", "padronizacao", "licoes", "ferramentas_aplicadas",
]
