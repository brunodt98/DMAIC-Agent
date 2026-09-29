"""
ui/theme.py — Identidade visual da aplicação.

Tudo que é aparência mora aqui; o método DMAIC mora em core/metodo.py.

As cores são declaradas uma vez como variáveis CSS e referenciadas por nome.
Hex repetido pelo código é como a interface fica desalinhada aos poucos: muda
num lugar, esquece no outro.

Sobre os seletores: os que começam com `.dmaic-` são de marcação escrita por
esta aplicação e não mudam. Os que usam `data-testid` são do Streamlit —
estáveis entre versões, ao contrário das classes com hash que ele gera. Se
alguma regra do Streamlit parar de casar numa versão futura, a interface perde
o refinamento mas continua legível.
"""

from __future__ import annotations

PAGE_CONFIG = dict(
    page_title="DMAIC Agent",
    page_icon=":material/track_changes:",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    /* Superfícies, do fundo para a frente */
    --fundo:        #0B0E14;
    --superficie:   #131822;
    --superficie-2: #1A2130;
    --borda:        #262E3F;
    --borda-clara:  #34405A;

    /* Texto */
    --texto:        #E7EAF0;
    --texto-suave:  #9AA3B7;
    --texto-fraco:  #667085;

    /* Estados: azul é onde estamos, verde é o que ficou pronto */
    --acento:        #4D9FFF;
    --acento-fundo:  rgba(77, 159, 255, .12);
    --ok:            #34D399;
    --ok-fundo:      rgba(52, 211, 153, .12);
    --atencao:       #FBBF24;
    --atencao-fundo: rgba(251, 191, 36, .12);

    --raio:   10px;
    --raio-g: 14px;
}

/* ── Base ─────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background: var(--fundo); color: var(--texto); }

/* O padrão do Streamlit reserva espaço para um cabeçalho que não usamos. */
[data-testid="stMainBlockContainer"],
.block-container {
    padding-top: 2.2rem;
    padding-bottom: 6rem;
    max-width: 1080px;
}
[data-testid="stHeader"] { background: transparent; }
hr { border-color: var(--borda); opacity: .7; }

h1, h2, h3, h4 { letter-spacing: -.02em; font-weight: 600; color: var(--texto); }
p, li, .stMarkdown { line-height: 1.65; }

/* ── Marca ────────────────────────────────────────────────────── */
.dmaic-marca {
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 1.6rem;
}
/* Cinco barras: as etapas do método, em miniatura. */
.dmaic-glifo {
    display: flex; align-items: flex-end; gap: 3px;
    height: 34px; padding: 6px 8px;
    background: var(--superficie); border: 1px solid var(--borda);
    border-radius: var(--raio);
}
.dmaic-glifo i {
    display: block; width: 3px; border-radius: 2px; background: var(--acento);
}
.dmaic-glifo i:nth-child(1) { height:  7px; opacity: .35; }
.dmaic-glifo i:nth-child(2) { height: 11px; opacity: .5;  }
.dmaic-glifo i:nth-child(3) { height: 15px; opacity: .65; }
.dmaic-glifo i:nth-child(4) { height: 19px; opacity: .8;  }
.dmaic-glifo i:nth-child(5) { height: 23px; opacity: 1;   }

.dmaic-marca-nome {
    font-size: 1.45rem; font-weight: 700; line-height: 1.15;
    letter-spacing: -.03em;
}
.dmaic-marca-sub {
    font-size: .8rem; color: var(--texto-fraco); margin-top: 2px;
}
.dmaic-marca-ctx {
    margin-left: auto; text-align: right;
    font-size: .78rem; color: var(--texto-suave); line-height: 1.5;
}
.dmaic-marca-ctx b { color: var(--texto); font-weight: 500; }

/* ── Trilha das etapas ────────────────────────────────────────── */
.dmaic-trilha { display: flex; margin: 0 0 .4rem; }
.dmaic-passo {
    flex: 1; position: relative; text-align: center; padding-top: 4px;
}
/* Os dois traços que ligam um passo ao vizinho. */
.dmaic-passo::before, .dmaic-passo::after {
    content: ""; position: absolute; top: 21px; height: 2px;
    background: var(--borda); z-index: 0;
}
.dmaic-passo::before { left: 0;   right: 50%; }
.dmaic-passo::after  { left: 50%; right: 0;   }
.dmaic-passo:first-child::before,
.dmaic-passo:last-child::after { display: none; }

/* O traço fica aceso até onde o projeto chegou. */
.dmaic-passo.feito::before, .dmaic-passo.feito::after,
.dmaic-passo.atual::before { background: var(--ok); }

.dmaic-selo {
    position: relative; z-index: 1;
    width: 40px; height: 40px; margin: 0 auto 8px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%; font-size: .9rem; font-weight: 700;
    background: var(--fundo); border: 2px solid var(--borda);
    color: var(--texto-fraco);
    transition: all .18s ease;
}
.dmaic-passo.feito .dmaic-selo {
    background: var(--ok-fundo); border-color: var(--ok); color: var(--ok);
}
.dmaic-passo.atual .dmaic-selo {
    background: var(--acento-fundo); border-color: var(--acento);
    color: var(--acento);
    box-shadow: 0 0 0 5px var(--acento-fundo);
}
.dmaic-nome {
    display: block; font-size: .82rem; font-weight: 500;
    color: var(--texto-fraco);
}
.dmaic-passo.feito .dmaic-nome { color: var(--texto-suave); }
.dmaic-passo.atual .dmaic-nome { color: var(--texto); font-weight: 600; }
.dmaic-dica {
    display: block; font-size: .7rem; color: var(--texto-fraco);
    margin-top: 3px; padding: 0 6px; line-height: 1.35;
}
.dmaic-passo:not(.atual) .dmaic-dica { opacity: 0; }

/* ── Faixa de aviso (espera de campo) ─────────────────────────── */
.dmaic-faixa {
    display: flex; gap: 12px; align-items: stretch;
    background: var(--atencao-fundo);
    border: 1px solid rgba(251, 191, 36, .3);
    border-radius: var(--raio); padding: 12px 14px;
    font-size: .85rem; color: var(--texto); line-height: 1.55;
    margin: 1rem 0 .2rem;
}
.dmaic-faixa-borda {
    width: 3px; border-radius: 3px;
    background: var(--atencao); flex: 0 0 3px;
}
.dmaic-faixa b { color: var(--atencao); }

/* ── Conversa ─────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent; padding: .5rem 0; gap: 14px;
}
/* A fala vira um cartão; o avatar fica fora dele. */
[data-testid="stChatMessage"] > div:last-child {
    background: var(--superficie);
    border: 1px solid var(--borda);
    border-radius: var(--raio-g);
    padding: 14px 18px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > div:last-child {
    background: var(--superficie-2);
    border-color: var(--borda-clara);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) > div:last-child {
    border-left: 3px solid var(--acento);
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--acento-fundo) !important;
    color: var(--acento) !important;
    border: 1px solid rgba(77, 159, 255, .35);
}
[data-testid="stChatMessageAvatarUser"] {
    background: var(--superficie-2) !important;
    color: var(--texto-suave) !important;
    border: 1px solid var(--borda);
}
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4 { font-size: 1rem; margin-top: .9rem; }
[data-testid="stChatMessage"] strong { color: #FFF; font-weight: 600; }

[data-testid="stChatInput"] textarea { font-family: 'Inter', sans-serif; }
[data-testid="stBottomBlockContainer"] { background: var(--fundo); }

/* ── Barra lateral ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--superficie);
    border-right: 1px solid var(--borda);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .55rem; }
.dmaic-secao {
    font-size: .68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .09em; color: var(--texto-fraco);
    margin: .5rem 0 .1rem;
}

/* Lista de progresso da lateral */
.dmaic-lista { display: flex; flex-direction: column; gap: 5px; }
.dmaic-item {
    display: flex; align-items: center; gap: 9px;
    font-size: .82rem; color: var(--texto-fraco); padding: 3px 0;
}
.dmaic-bolha {
    width: 20px; height: 20px; flex: 0 0 20px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%; font-size: .62rem; font-weight: 700;
    border: 1.5px solid var(--borda); color: var(--texto-fraco);
}
.dmaic-item.feito { color: var(--texto-suave); }
.dmaic-item.feito .dmaic-bolha {
    background: var(--ok-fundo); border-color: var(--ok); color: var(--ok);
}
.dmaic-item.atual { color: var(--texto); font-weight: 600; }
.dmaic-item.atual .dmaic-bolha {
    background: var(--acento-fundo); border-color: var(--acento);
    color: var(--acento);
}

/* Etiquetas das ferramentas aplicadas */
.dmaic-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 2px; }
.dmaic-tag {
    font-size: .7rem; padding: 3px 8px; border-radius: 20px;
    background: var(--ok-fundo); color: var(--ok);
    border: 1px solid rgba(52, 211, 153, .28);
}

/* ── Controles ────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: var(--raio); font-weight: 500; font-size: .85rem;
    border: 1px solid var(--borda-clara); background: var(--superficie-2);
    color: var(--texto); transition: all .15s ease;
}
.stButton > button:hover:not(:disabled),
.stDownloadButton > button:hover:not(:disabled),
.stFormSubmitButton > button:hover:not(:disabled) {
    border-color: var(--acento); color: var(--acento);
    background: var(--acento-fundo);
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: var(--acento); border-color: var(--acento); color: #06101F;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover:not(:disabled),
.stDownloadButton > button[kind="primary"]:hover:not(:disabled),
.stFormSubmitButton > button[kind="primary"]:hover:not(:disabled) {
    filter: brightness(1.1); color: #06101F;
}
.stButton > button:disabled, .stFormSubmitButton > button:disabled { opacity: .45; }

[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stChatInput"] > div {
    background: var(--superficie-2) !important;
    border-color: var(--borda) !important;
    border-radius: var(--raio) !important;
}
[data-testid="stTextInput"] input:focus { border-color: var(--acento) !important; }
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stCheckbox"] label {
    font-size: .78rem !important; color: var(--texto-suave) !important;
    font-weight: 500;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--superficie-2); border: 1px dashed var(--borda-clara);
    border-radius: var(--raio); padding: .8rem;
}

/* Caixas nativas de aviso: mais planas, sem o degradê do padrão. */
[data-testid="stAlert"], .stAlert {
    border-radius: var(--raio); border: 1px solid var(--borda);
    font-size: .83rem; padding: .7rem .9rem;
}
[data-testid="stAlert"] p { line-height: 1.55; margin-bottom: 0; }
[data-testid="stCaptionContainer"], .stCaption {
    color: var(--texto-fraco) !important; font-size: .76rem !important;
}

/* ── Telas estreitas ──────────────────────────────────────────── */
@media (max-width: 760px) {
    .dmaic-dica { display: none; }
    .dmaic-selo { width: 34px; height: 34px; font-size: .8rem; }
    .dmaic-passo::before, .dmaic-passo::after { top: 18px; }
    .dmaic-nome { font-size: .7rem; }
    .dmaic-marca-ctx { display: none; }
    [data-testid="stMainBlockContainer"], .block-container {
        padding-left: 1rem; padding-right: 1rem;
    }
}
</style>
"""
