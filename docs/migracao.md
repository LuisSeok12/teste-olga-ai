# Migração para Produção (n8n → Kestra)

## Objetivo
Reusar a mesma lógica de negócio em produção, apenas trocando o orquestrador.

## Plano
1) **Preparação**
   - Extrair lógica de fila/roteamento para a API (já feito).
   - Definir contratos HTTP / payloads estáveis.

2) **Job Equivalente no Kestra**
   - Tarefas:
     - Buscar lote (`/api/queue/next`)
     - Roteamento (`/api/router/route`)
     - Concluir (`/queue/{id}/complete`) ou erro (`/queue/{id}/error`)
   - Agendador: CRON a cada 1 min (ou 10s em pico).

3) **Testes Paralelos**
   - Rodar n8n e Kestra em paralelo consumindo subconjuntos (ex.: mod 2 de IDs).
   - Validar consistência (CONCLUIDO/ERRO) e tempos.

4) **Cutover Gradual**
   - 10% → 50% → 100% do tráfego sob Kestra.
   - Feature flag para rollback instantâneo ao n8n se necessário.

5) **Monitoramento**
   - Métricas: profundidade da fila, taxa de erro, latência, retries.
   - Alarmes por SLA violado (ex.: item > X minutos em AGUARDANDO).


