"""
ui/theme.py — Configuração da página e CSS global.

Aparência fica aqui; o método DMAIC fica em core/metodo.py.
"""

PAGE_CONFIG = dict(
    page_title="DMAIC Agent",
    page_icon=":material/track_changes:",
    layout="wide",
)

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
