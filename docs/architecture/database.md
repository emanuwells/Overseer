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

## Tabelas ativas

| Grupo | Tabelas |
|---|---|
| Canónicas (`overseer_*`) | `overseer_pipelines`, `overseer_pipeline_nodes`, `overseer_pipeline_edges`, `overseer_runs`, `overseer_modules`, `overseer_logs`, `overseer_heartbeats`, `overseer_triggers` |
| Governação (MAIATRON-HUB) | `overseer_identity_mappings`, `overseer_identity_mapping_requests`, `overseer_permission_requests`, `overseer_pipeline_permissions` |

Tabelas legado (`pipeline_*`, `orchestrator_*_local`, medidata, alertas antigos) foram removidas do schema de produção. Para auditoria ou drop em outros ambientes: `scripts/audit_db_schema.py` e `scripts/drop_legacy_tables.py`.

## Migrações E Compatibilidade

- Alterações de schema devem ser pequenas, reversíveis quando possível e cobertas por testes.
- Dados fora do contrato `overseer_*` e governação listada acima não são fonte ativa.
- Campos JSON devem degradar de forma tolerante quando payloads externos tiverem informação parcial.

## Segurança

- URLs de base de dados e credenciais reais não devem ser versionadas.
- Exemplos devem usar valores locais seguros e claramente substituíveis.
- Dumps, backups e ficheiros locais de runtime não devem ser apagados ou alterados sem confirmação explícita.
