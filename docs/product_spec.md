# DMAIC Agent — Especificação do Produto

> Documento interno de referência para o comportamento e visão da ferramenta.

Este arquivo documenta a especificação completa do produto conforme definida por Bruno Silva.
O arquivo completo está disponível no prompt de produto original e deve ser mantido aqui
como referência para desenvolvimento futuro e onboarding de colaboradores.

## Resumo executivo

O DMAIC Agent é o único consultor Six Sigma que:
- Aplica as ferramentas certas no momento certo (sem perguntar ao usuário qual usar)
- Sabe a hora de parar de perguntar (Protocolo de Campo)
- Monta o plano para o usuário ir buscar o que falta
- Entrega o documento que leva ao campo — e traz de volta

## Ciclo completo esperado

```
Usuário descreve o problema
        ↓
Consultor aplica Funil de Problemas para refinar o escopo
        ↓
Consultor faz perguntas, aprofunda e aplica ferramentas da etapa
        ↓
Usuário trava (não tem dados)
        ↓
Consultor detecta o bloqueio
        ↓
Protocolo de Campo acionado (Plano + Síntese + PARAR)
        ↓
Documento Word gerado automaticamente
        ↓
Usuário vai ao campo com o documento
        ↓
Usuário volta com os dados
        ↓
Consultor retoma, valida o que foi coletado e continua
        ↓
Projeto avança para a próxima etapa
        ↓
(ciclo se repete até o CONTROLAR estar completo)
```

## Para a especificação completa

Consulte o documento `product_spec.md` recebido do autor do projeto.
