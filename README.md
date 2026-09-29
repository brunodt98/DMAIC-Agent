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
│   ├── state.py              # Única ponte com o session_state do Streamlit
│   │
│   ├── core/                 # Núcleo — não conhece Streamlit
│   │   ├── metodo.py         # O método DMAIC como dado: etapas, ferramentas, campos
│   │   ├── llm.py            # Acesso aos provedores (Groq e OpenRouter)
│   │   ├── prompt.py         # System prompt do consultor
│   │   ├── agent.py          # O consultor: o que pedir e como ler a resposta
│   │   └── export/
│   │       └── word.py       # Gerador do documento Word (.docx)
│   │
│   └── ui/                   # Componentes de interface
│       ├── __init__.py
│       ├── theme.py          # Configuração da página e CSS
│       ├── sidebar.py        # Provedor, modelo, retomada, progresso, exportação
│       ├── header.py         # Cabeçalho e barra de progresso DMAIC
│       ├── onboarding.py     # Tela inicial de cadastro do projeto
│       └── chat.py           # Conversa e resposta em fluxo
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
- Uma chave de API de um dos provedores suportados:
  [Groq](https://console.groq.com/keys) (gratuita) ou
  [OpenRouter](https://openrouter.ai/settings/keys) (tem modelos gratuitos)

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

Na barra lateral, escolha o provedor e cole sua chave. Ela **não é armazenada** em
nenhum arquivo — permanece apenas na sessão do navegador, e sobrevive a "Novo
projeto" para você não precisar digitar de novo.

| Provedor | Onde obter | Observação |
|---|---|---|
| Groq | [console.groq.com/keys](https://console.groq.com/keys) | Gratuito e rápido |
| OpenRouter | [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) | Muitos modelos, vários gratuitos |

### Modelo LLM

A lista de modelos é buscada no provedor no momento em que você informa a chave,
não fica escrita no código. Modelo descontinuado simplesmente deixa de aparecer,
em vez de devolver um erro 404 no meio da conversa.

O seletor mostra o tamanho do contexto de cada modelo e marca os gratuitos. A
primeira opção é a recomendada para o provedor escolhido.

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

Há dois caminhos, para situações diferentes.

**Arquivo de projeto** — guarda a sessão inteira: conversa, dados apurados,
etapa e ferramentas aplicadas.

1. Em **Projeto**, clique em **Salvar projeto** e guarde o `.dmaic.json`
2. Para voltar, faça upload do mesmo arquivo em **Abrir projeto**
3. A sessão volta exatamente de onde parou

**Documento Word** — para quando o projeto avançou no campo, fora da
aplicação, e o que existe é o `.docx`.

1. Na barra lateral, vá em **Retomar projeto**
2. Faça upload do `.docx` gerado anteriormente
3. O consultor lê o documento, identifica onde parou e continua

### Recuperação após F5

Rodando na sua máquina, a sessão é gravada em disco a cada resposta e volta
sozinha se você recarregar a página. O aviso *Sessão recuperada* aparece na
barra lateral, e o interruptor **Recuperar sessão após F5** desliga o
comportamento.

Os arquivos ficam em `~/.dmaic_agent` (ou no caminho de `DMAIC_DATA_DIR`),
fora do repositório.

Em acesso remoto o autosave não entra: como a gravação é em disco, num
servidor compartilhado o projeto de um usuário apareceria para o próximo.
Nesse caso, salve o projeto em arquivo antes de fechar.

---

## Arquitetura de decisões

| Decisão | Motivo |
|---|---|
| `core/` sem Streamlit | O núcleo recebe estado por parâmetro e devolve valores, então dá para testá-lo sem subir a aplicação |
| `state.py` como única ponte | Um só dono do `session_state`; o resto do código não escreve nele por conta própria |
| `core/prompt.py` separado de `core/agent.py` | Permite iterar no comportamento do agente sem tocar na lógica de chamada |
| `core/metodo.py` | O método DMAIC como dado — etapas, ferramentas, campos — em vez de strings espalhadas pelo código |
| Rodapé de marcadores na resposta | O consultor declara etapa e ferramentas aplicadas; detectar por palavra-chave fazia o app pular de etapa só porque a palavra "medir" apareceu numa frase |
| Modelos buscados no provedor | Lista fixa no código envelhece e o usuário recebe 404 sem explicação |
| Subpacote `ui/` | Cada componente visual tem responsabilidade única e pode ser testado isoladamente |
| `core/export/word.py` com classe `DocBuilder` | Helpers reutilizáveis; o documento cresce sem duplicar código de formatação |

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
