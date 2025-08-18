# Análise e Diagnóstico

## 1.1 Fila de Atendimento
- **Garantia de resposta**: persistir solicitações em `atendimento_queue` (PostgreSQL).
- **Prioridade/ordem**: seleção por `ORDER BY priority ASC, created_at ASC`.
- **Controle de pico**: consumo em lotes (`batchSize`) no worker n8n; reexecução periódica por schedule.

## 1.2 Roteamento
- **Com apólice ativa** → fluxo `SINISTRO` (ou `SINISTRO_INTAKE` para coleta inicial).
- **Sem apólice** → fluxo `VENDAS/REATIVACAO`.
- **Desconhecido** → fluxo `TRIAGEM` (coleta de dados mínimos).
- Implementado via endpoint `/api/router/route` com regras simples de texto/cliente.

## 1.3 Por que “tools” em vez de muitos nodes (n8n)?
- **Estabilidade**: menos dependência entre nós; um HTTP “tool” centraliza erros/retries.
- **Reuso**: mesma tool chamada por vários fluxos (ex.: `QueueManager`, `CustomerRouter`).
- **Versionamento/teste**: lógica fica em código (Git, testes), UI só orquestra.

## 1.4 Estratégia de Migração (n8n → produção)
- Manter **lógica em serviços** (API) e usar o n8n apenas como “caller”.
- Mapear 1:1 as chamadas para o orquestrador de produção (Kestra).
- Garantir idempotência e observabilidade (logs, métricas) nos serviços.
