# Decisões de Arquitetura e Projeto

## 🎯 Objetivo
Registrar as principais escolhas feitas no desenvolvimento do teste técnico, com justificativas e trade-offs.

---

## 1. Banco de Dados: PostgreSQL
**Decisão:** Utilizar o PostgreSQL como fila persistente (`atendimento_queue`).  
**Justificativa:**  
- Já disponível em Docker oficial.  
- Suporta transações, índices e consultas eficientes para ordenação por prioridade.  
- Evita dependência adicional (ex.: Redis, RabbitMQ).  

**Trade-off:**  
- Postgres não é ideal para filas de alta concorrência.  
- Em produção, um **broker dedicado** (Kafka, RabbitMQ, SQS) pode ser melhor.

---

## 2. Fila no Banco
**Decisão:** Implementar fila dentro da tabela `atendimento_queue`.  
**Justificativa:**  
- Simplicidade → um único sistema de persistência.  
- Permite histórico de atendimentos (auditoria).  
- Facilita consultas manuais para debugging.

**Alternativa descartada:**  
- Usar fila em memória (não persistente) → risco de perda de dados em falha.

---

## 3. Orquestração: n8n
**Decisão:** Implementar o worker no **n8n**.  
**Justificativa:**  
- Fácil visualização de fluxo.  
- Baixa curva de aprendizado.  
- Suporta retries, condições e integrações.  

**Trade-off:**  
- Workflows em UI são menos versionáveis do que código puro.  
- Testes automatizados são mais limitados.  

---

## 4. API de Intermediação
**Decisão:** Criar API em FastAPI (Python) para centralizar regras.  
**Responsabilidades:**  
- CRUD da fila.  
- Roteamento por tipo de mensagem.  
- Encerramento de atendimentos (sucesso/erro).  

**Justificativa:**  
- Separa lógica de negócio do workflow.  
- Facilita testes manuais via HTTP.  
- Reuso em outros orquestradores (ex.: Kestra).

---

## 5. Roteamento de Clientes
**Decisão:** Regras simples baseadas em texto da mensagem.  
Exemplo: mensagens contendo `"sinistro"` → fluxo **SINISTRO**.  

**Justificativa:**  
- Atende ao escopo do teste.  
- Permite expansão futura para **classificação por IA/ML**.

---

## 6. Erros e Retentativas
**Decisão:**  
- Em caso de falha → marcar item como `FALHA` e reencaminhar para fila.  
- Controlado pelo workflow n8n (`Has Error?` + `Mark Error`).  

**Justificativa:**  
- Garante que nenhum atendimento se perca.  
- Possibilita retry manual ou automático.

---

## 7. Kestra
**Decisão:** Deixado de fora da entrega.  
**Justificativa:**  
- Complexidade adicional.  
- Optado por deixar de fora por falta de conhecimento sobre a ferramenta.

---

## 8. Docker Compose
**Decisão:** Usar `docker-compose` para levantar todo o ambiente.  
**Serviços:**  
- `db` → PostgreSQL  
- `adminer` → interface de DB  
- `n8n` → workflow engine  
- (Kestra planejado mas desabilitado)  

**Justificativa:**  
- Facilidade de setup → um comando levanta tudo.  
- Portabilidade → funciona em qualquer ambiente com Docker.

---

## 9. Escopo Entregue
- ✅ Fila no Postgres  
- ✅ API interna em FastAPI  
- ✅ Workflow funcional em n8n  
- ✅ Testes ponta a ponta validados  
- ❌ Kestra (planejado, não validado)  

---

## 10. Próximos Passos (Evolução)
- Integrar Kestra como alternativa/backup ao n8n.  
- Implementar **Dead Letter Queue (DLQ)** para falhas críticas.  
- Adicionar métricas (Prometheus + Grafana).  
- Substituir regras simples por **classificação automática de intenções (NLP)**.  
- Testes automatizados de integração (Pytest + Testcontainers).
