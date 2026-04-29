# 🎯 DMAIC Agent

> Consultor Six Sigma com Inteligência Artificial — conduz projetos de melhoria de processos de forma conversacional, como um Master Black Belt experiente faria numa reunião real.

**Projeto de Bruno Silva — Estudante de Ciência de Dados · FATEC Cotia × Outtech Services IT**

---

## O que é

O DMAIC Agent é uma aplicação web que substitui formulários estáticos por uma conversa inteligente. O usuário chega com um problema real — às vezes mal definido, sem todos os dados — e o agente conduz o raciocínio pelas 5 etapas do método DMAIC:

```
🎯 DEFINIR → 📏 MEDIR → 🔍 ANALISAR → 🚀 MELHORAR → 📊 CONTROLAR
```

Quando o usuário não tem um dado disponível, o agente **para de perguntar**, monta um **Plano de Campo** com as tarefas concretas para ir buscar essa informação, e gera automaticamente um documento Word para levar ao campo.

---

## Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **Consulta conversacional** | 1 pergunta por vez, contextualizada ao problema real |
| **Ferramentas DMAIC aplicadas** | Ishikawa, 5 Porquês, SIPOC, Pareto, FMEA, 5W2H, Funil de Problemas e outras — conduzidas na conversa |
| **Detecção automática de bloqueio** | Identifica quando o usuário não tem o dado disponível e aciona o Protocolo de Campo |
| **Plano de Campo** | Documento estruturado com o que levantar, onde, quem faz, como e prazo |
| **Síntese da Sessão** | Consolida tudo que foi construído + compromisso do próximo passo |
| **Documento Word automático** | Gerado automaticamente ao acionar o Protocolo de Campo |
| **Retomada de projeto** | Upload do .docx preenchido — o agente lê, identifica onde parou e continua |
| **Rastreamento de etapa** | Progresso visual pelas 5 etapas, atualizado automaticamente |

---

## Estrutura do projeto

```
dmaic_agent/
│
├── app.py                    # Ponto de entrada — monta a aplicação
│
├── dmaic/                    # Pacote principal
│   ├── __init__.py
│   ├── config.py             # Constantes, CSS, roadmap, mapeamento de ferramentas
│   ├── state.py              # Inicialização e gestão do session_state
│   ├── prompt.py             # System prompt do consultor (separado para versionamento)
│   ├── ai.py                 # Todas as chamadas à API Groq
│   ├── document.py           # Gerador do documento Word (.docx)
│   │
│   └── ui/                   # Componentes de interface
│       ├── __init__.py
│       ├── sidebar.py        # Barra lateral: API key, upload, progresso, exportação
│       ├── header.py         # Cabeçalho e barra de progresso DMAIC
│       ├── onboarding.py     # Tela inicial de cadastro do projeto
│       └── chat.py           # Histórico de chat e tratamento de input
│
├── docs/
│   └── product_spec.md       # Especificação completa do produto
│
├── .streamlit/
│   └── config.toml           # Tema visual da aplicação
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Instalação e execução

### Pré-requisitos

- Python 3.11+
- Conta gratuita no [Groq Console](https://console.groq.com/keys) para obter a API Key

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/dmaic-agent.git
cd dmaic-agent

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`.

---

## Configuração

### API Key

Na barra lateral da aplicação, insira sua API Key do Groq. Ela **não é armazenada** em nenhum arquivo — permanece apenas na sessão do navegador.

Para configuração persistente (opcional), crie o arquivo `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "sua-chave-aqui"
```

### Modelo LLM

O modelo padrão é `llama-3.3-70b-versatile`. Outros modelos disponíveis:

| Modelo | Característica |
|---|---|
| `llama-3.3-70b-versatile` | Recomendado — melhor equilíbrio qualidade/velocidade |
| `llama3-70b-8192` | Contexto maior, mais lento |
| `mixtral-8x7b-32768` | Contexto muito grande, bom para conversas longas |

---

## Como usar

### Iniciando um projeto novo

1. Preencha **Empresa** e **Responsável** (obrigatórios) na tela inicial
2. Descreva o problema com suas palavras — sem formato específico
3. Responda as perguntas do consultor; ele conduz tudo

### Quando o consultor acionar o Plano de Campo

1. Leia o Plano de Campo e a Síntese da Sessão
2. Clique em **Gerar Word** na barra lateral (ou aguarde a geração automática)
3. Baixe o `.docx` e leve para o campo / envie aos responsáveis
4. Execute as tarefas levantadas
5. Volte à aplicação, faça upload do documento preenchido ou continue a conversa

### Retomando um projeto existente

1. Na barra lateral, clique em **📂 Retomar projeto**
2. Faça upload do `.docx` gerado anteriormente
3. O consultor lê o documento, identifica onde parou e continua

---

## Arquitetura de decisões

| Decisão | Motivo |
|---|---|
| `prompt.py` separado de `ai.py` | Permite iterar no comportamento do agente sem tocar na lógica de chamada |
| `config.py` centralizado | Todas as constantes em um lugar — roadmap, ferramentas, campos — evita magic strings espalhadas |
| `state.py` isolado | Inicialização e mutação do estado em funções nomeadas, não inline |
| Subpacote `ui/` | Cada componente visual tem responsabilidade única e pode ser testado isoladamente |
| `document.py` com classe `DocBuilder` | Helpers reutilizáveis; o documento cresce sem duplicar código de formatação |

---

## Ferramentas DMAIC suportadas

| Etapa | Ferramentas |
|---|---|
| **Definir** | Funil de Problemas, SIPOC, VOC, CTQ, Project Charter |
| **Medir** | Mapa de Processo, Plano de Coleta, Baseline, Pareto, MSA |
| **Analisar** | Ishikawa (6M), 5 Porquês, Matriz de Priorização, Estratificação |
| **Melhorar** | Brainstorming, Matriz Esforço×Impacto, FMEA, 5W2H |
| **Controlar** | Gráfico de Controle (CEP), Plano de Controle, SOP, Lições Aprendidas |

---

## Licença

Este projeto é de uso acadêmico e educacional.  
**Bruno Silva — FATEC Cotia · Ciência de Dados**
