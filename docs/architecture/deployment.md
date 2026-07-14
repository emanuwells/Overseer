# Arquitetura De Deploy E Operação

## Responsabilidade

O fluxo oficial do Overseer é Docker-first. O Compose local/prod arranca API, SPA React servida pela API (ou nginx em `/Overseer/`) e base de dados relacional, com scripts auxiliares para provisionamento, manutenção e integração de runners externos.

## Ambientes

| Ambiente | Entrada Principal | Observações |
|---|---|---|
| Desenvolvimento local | `docker compose --project-directory . --env-file secrets/.env -f docker/docker-compose.yml up --build -d` | Caminho recomendado para API, UI e MariaDB local |
| Produção | `docker compose --project-directory . --env-file secrets/.env -f docker/docker-compose.prod.yml up --build -d` | UI pública em `/Overseer/` via nginx |
| Windows runners | `scripts/windows/*` | Provisionamento, Task Scheduler, heartbeat e túnel SSH |
| Linux runners | `scripts/provision-runners.sh` e templates | Integração externa sem executar pipelines no núcleo |

## Configuração

- Variáveis de ambiente ficam em `secrets/.env` (template em `docs/resources/templates/.env.example`).
- Configuração de SSH, tokens, webhooks e DB real deve permanecer fora do Git.

## Validação Operacional

- `python -m pytest -q` valida comportamento técnico.
- `docker compose --project-directory . -f docker/docker-compose.yml config` valida estrutura Compose sem subir serviços.
- Health local esperado: `http://127.0.0.1:8090/v1/health`.
- UI local esperada: `http://127.0.0.1:8090/ui/`.

## Regras De Segurança

- Não executar deploy, SSH, restart de serviços ou alterações em produção sem confirmação explícita.
- Não alterar CI/CD, Compose ou Dockerfile sem plano e validação própria.
- Não apagar volumes, backups, bases de dados ou runtime local sem autorização específica.
