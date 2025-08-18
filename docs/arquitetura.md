# Arquitetura da Solução

## Visão Geral

A solução implementa uma **fila de atendimentos** persistida em PostgreSQL e um **worker em n8n** que:

1. busca itens aguardando processamento,
2. roteia o atendimento (ex.: sinistro vs. outros),
3. conclui com resultado ou registra erro e reencaminha.

> **Escopo de entrega**: Docker + Postgres + API + Workflow n8n (testado). Kestra ficou **planejado** e documentado como evolução, mas não foi incluído na execução final.

---

## Diagrama (alto nível)

```mermaid
flowchart LR
  A[Cliente / Webhook] -->|/api/queue/add| B[(PostgreSQL)]
  subgraph API (FastAPI)
    A1[/Queue Router/]
    A2[/Customer Router/]
  end
  B <-->|SELECT/UPDATE| API
  subgraph n8n Worker
    W1[Queue Next] --> W2[For Each]
    W2 --> W3[Route]
    W3 --> W4{Has Error?}
    W4 -- false --> W5[Branch]
    W5 -- SINISTRO --> W6[Process Sinistro (mock)]
    W5 -- Outros --> W7[Process Outros (mock)]
    W4 -- true --> W8[Mark Error]
    W6 -->|/complete| API
    W7 -->|/complete| API
    W8 -->|/error| API
  end
  API -->|/complete, /error| B
```

---

## Componentes

### Banco de Dados (PostgreSQL)

Tabela principal: `atendimento_queue`.

```sql
CREATE TABLE atendimento_queue (
  id             SERIAL PRIMARY KEY,
  phone          TEXT NOT NULL,
  message        TEXT NOT NULL,
  priority       INT  NOT NULL DEFAULT 5, -- menor = mais urgente
  status         TEXT NOT NULL DEFAULT 'AGUARDANDO', -- AGUARDANDO|PROCESSANDO|CONCLUIDO|FALHA
  result         JSONB,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON atendimento_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_priority_created
  ON atendimento_queue(priority ASC, created_at ASC);
```

**Estados:**

* `AGUARDANDO`: pronto para ser consumido
* `PROCESSANDO`: em processamento pelo worker
* `CONCLUIDO`: finalizado com sucesso (possui `result`)
* `FALHA`: encerrado por erro (opcional – pode reencaminhar com política de retry)

---

### API (serviço interno)

Responsável por intermediar o worker e a fila.

**Principais endpoints**

```
POST /api/queue/add
  body: { phone, message, priority? } -> { id, position, estimated_wait }

POST /api/queue/next
  body: { batchSize } -> [ { id, phone, message, priority } ]

POST /api/queue/{id}/complete
  body: { status: "OK", ... } -> { ok: true }

POST /api/queue/{id}/error
  body: { error } -> { ok: true }

POST /api/router/route
  body: { phone, message } -> { flow, subworkflow?, customer_data?, next_action }
```

**Regras-chave:**

* `/queue/next` prioriza `priority ASC` e `created_at ASC`.
* `/complete` e `/error` atualizam `status` (`CONCLUIDO` ou `AGUARDANDO/FALHA`) e `updated_at`.
* `/router/route` decide o **fluxo** (ex.: `SINISTRO` vs `Outros`) por regras simples de conteúdo.

---

### Worker (n8n)

Fluxo testado e exportado em `n8n/workflows.json`.

**Nós principais**:

* **Queue Next (HTTP)** → chama `/api/queue/next`
* **For Each** → itera cada item retornado
* **Route (HTTP)** → chama `/api/router/route`
* **Has Error? (IF)** → condição: `statusCode >= 400` (somente erro real)
* **Branch (IF)** → `flow == SINISTRO` ou `SINISTRO_INTAKE` → branch de sinistro; caso contrário → outros
* **Process Sinistro / Outros (HTTP)** → chamam `/queue/{id}/complete` com JSON de resultado
* **Mark Error (HTTP)** → chama `/queue/{id}/error` com mensagem
* **Loop back** do No-Op → volta para `For Each` (garante consumo contínuo)

**Resiliência**:

* `Continue On Fail = true` nos HTTP
* Timeouts e retries configuráveis nos nós de rede
* `Has Error?` só considera erro real (evita falsos positivos)

---

## Prioridade & Ordenação

* Quanto **menor** o `priority`, **maior** a urgência.
* Seleção dos próximos itens: `ORDER BY priority ASC, created_at ASC`.
* Permite `batchSize` ajustável para escoar picos.

---

## Estimativa de Espera

Cálculo simples: `position * tempo_médio_por_atendimento`.
Exposto no retorno de `/queue/add` como `estimated_wait` (ex.: `~5 min`).

---

## Observabilidade

* Consultas manuais:

  ```bash
  docker compose -f docker/docker-compose.yml exec -T db \
    psql -U olga -d olga_ai -c "SELECT id, status, result FROM atendimento_queue ORDER BY id DESC LIMIT 10;"
  ```
* Logs do n8n no container.
* Possível evolução: métricas (prometheus), tracing (OTel), dashboards (Grafana).

---

## Segurança & Configuração

* **Segredos** via variáveis de ambiente (senhas de DB).
* **CORS** e **rate limit** podem ser adicionados na API caso haja exposição externa.
* Por padrão, a API é usada **internamente** (localhost / Docker host).

**Variáveis relevantes**

```
POSTGRES_USER=olga
POSTGRES_PASSWORD=olga
POSTGRES_DB=olga_ai
API_BASE=http://127.0.0.1:3000
```

---

## Decisões de Arquitetura

* **n8n** como orquestrador: facilita visualizar, debugar e ajustar regras.
* **Fila no Postgres**: simplicidade e portabilidade; suficiente para o escopo do teste.
* **Mocks de serviços**: isolam a lógica da orquestração; pronto para trocar por integrações reais.

**Trade-offs**

* Postgres não é um broker dedicado (ex.: Rabbit/Kafka) → suficiente aqui, mas pode limitar alta escala.
* n8n é excelente para time-to-market, mas pipelines críticos podem exigir versionamento e testes adicionais.

---

## Evolução (futuro)

* **Kestra** (ou outro engine) para agendamento/observabilidade enterprise.
* **Retry com backoff** + **DLQ** (campo `attempt_count` e status `FALHA` com reprocessamento manual).
* **Idempotência** (campo `source_id` com UNIQUE para evitar duplicatas).
* **Classificação por IA** (substituir regras simples por modelo de intent).
* **Testes automáticos** (contratos de API, cenários de erro, carga).

---

## Como testar ponta a ponta (resumo)

1. **Subir**:

```bash
docker compose -f docker/docker-compose.yml up -d
```

2. **Adicionar item**:

```bash
curl -X POST http://127.0.0.1:3000/api/queue/add \
  -H "content-type: application/json" \
  -d '{"phone":"+5511999999999","message":"Preciso acionar sinistro","priority":3}'
```

3. **Verificar processamento**:

```bash
docker compose -f docker/docker-compose.yml exec -T db \
  psql -U olga -d olga_ai -c "SELECT id, status, result FROM atendimento_queue ORDER BY id DESC LIMIT 10;"
```

> Esperado: item sai de **AGUARDANDO** → **PROCESSANDO** → **CONCLUIDO** com `result`.
