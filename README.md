# Teste Técnico - Olga AI

Este é um teste tecnico que vai ser apagado e implementa um fluxo de automação para triagem e processamento de atendimentos em fila, utilizando **n8n**, **PostgreSQL** e **Docker**.

## Tecnologias
- [Docker](https://www.docker.com/) para orquestração
- [PostgreSQL](https://www.postgresql.org/) como banco de dados
- [n8n](https://n8n.io/) para orquestração de workflows
- API interna mockada para simulação de processamento

## Estrutura
- `docker/` → configurações do ambiente
- `n8n/` → export dos workflows criados e testados
- `docs/` → documentação técnica, diagramas e decisões

## Como rodar
1. Subir containers:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
````

2. Acessar:

   * n8n: [http://localhost:5678](http://localhost:5678)
   * DB (Postgres): porta `5432`, usuário `olga`, senha `olga`

3. Consultar a fila:

   ```bash
   docker compose -f docker/docker-compose.yml exec -T db \
     psql -U olga -d olga_ai -c "SELECT * FROM atendimento_queue ORDER BY id DESC LIMIT 10;"
   ```

## Fluxo n8n

O workflow implementa:

1. **Leitura da fila** (`Queue Next`)
2. **Iteração por item** (`For Each`)
3. **Roteamento por tipo** (`Route`)
4. **Validação de erro** (`Has Error?`)
5. **Encaminhamento para mocks de processamento**
6. **Registro de erros na fila (`Mark Error`)**

![Fluxo](docs/fluxo.png)

## Status

* Fluxo **n8n** validado e executando corretamente.
* Integração com DB funcionando.
* **Kestra** deixado de fora. Documentado em `docs/decisoes.md`.

## Próximos passos

* Melhorias de logging
* Expandir testes automatizados

````

---

### Exemplo de **docs/arquitetura.md**

```markdown
# Arquitetura da Solução

## Objetivo
Garantir que nenhum atendimento fique sem resposta, mantendo fila, priorização e roteamento adequado.

## Componentes
- **Fila (`atendimento_queue`)**: armazena atendimentos pendentes.
- **n8n Workflow**: responsável por consumir itens da fila, aplicar lógica de negócios e chamar mocks de serviços externos.
- **Mocks de Processamento**: simulam chamadas a sistemas de sinistro e outros fluxos.

## Fluxo Simplificado
1. Trigger agenda -> Leitura da fila.
2. Para cada atendimento:
   - Se erro → marca no banco.
   - Se válido → encaminha conforme regra de negócio.
3. Atualiza status no banco.
