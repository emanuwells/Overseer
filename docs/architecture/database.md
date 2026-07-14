# Arquitetura De Dados

## Responsabilidade

A camada de dados guarda o estado operacional do Overseer: catálogo de pipelines, nodes e edges de DAG, runs, eventos, heartbeats, triggers, deployments e metadados associados. As tabelas `overseer_*` são o contrato persistente ativo.

## Tecnologia

| Área | Tecnologia |
|---|---|
| Persistência local oficial | MariaDB via Docker Compose |
| Acesso relacional | SQLAlchemy |
| Configuração | `OVERSEER_DB_URL` e variáveis `MYSQL_*` |
| Desenvolvimento/testes | Dialectos SQLAlchemy compatíveis conforme testes e configuração |

## Modelo Operacional

- Pipelines externos registam catálogo por API.
- Runs, eventos e heartbeats são emitidos por SDK, agent ou integrações externas.
- A UI lê dados através de `/v1/read/*`; não escreve diretamente na base de dados.
- Triggers são registados como sinais operacionais e podem envolver dispatch externo configurado.

## Migrações E Compatibilidade

- Alterações de schema devem ser pequenas, reversíveis quando possível e cobertas por testes.
- Dados legados fora do contrato `overseer_*` não devem ser assumidos como fonte ativa sem decisão explícita.
- Campos JSON devem degradar de forma tolerante quando payloads externos tiverem informação parcial.

## Segurança

- URLs de base de dados e credenciais reais não devem ser versionadas.
- Exemplos devem usar valores locais seguros e claramente substituíveis.
- Dumps, backups e ficheiros locais de runtime não devem ser apagados ou alterados sem confirmação explícita.
