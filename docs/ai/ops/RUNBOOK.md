# Runbook

## Visão Geral

Este documento contém procedimentos operacionais para o Overseer.

## Ambiente

- **Produção**: Docker-first, auto-hosteado
- **Desenvolvimento**: Docker Compose local
- **Base de Dados**: MariaDB 10.11 (serviço `mysql` no Compose)

## Comandos Essenciais

Ver `COMMANDS.md` para lista completa.

### Startup

```bash
# Local
docker compose --project-directory . -f docker/docker-compose.yml up --build -d

# Produção (requer .env, OVERSEER_DB_URL, OVERSEER_RUNNERS_DIR, OVERSEER_RUNTIME_DIR)
docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
```

### Logs

```bash
docker compose --project-directory . -f docker/docker-compose.yml logs -f overseer-api
```

### Restore

```bash
# Exemplo com dump SQL — ajustar credenciais e contentor conforme o ambiente
docker compose --project-directory . -f docker/docker-compose.yml exec -T mysql \
  mariadb -u overseer -poverseer Overseer < backup.sql
```

## Monitorização

- Health check: `GET /v1/health`
- Interface web: `http://127.0.0.1:8090/ui/` (SPA React)
- Contrato API: `openapi/overseer-api.yaml`

## Troubleshooting

### API não responde

1. Verificar logs: `docker compose --project-directory . -f docker/docker-compose.yml logs overseer-api`
2. Verificar DB: `docker compose --project-directory . -f docker/docker-compose.yml exec mysql mariadb -u overseer -poverseer -e "SELECT 1"`
3. Reiniciar: `docker compose --project-directory . -f docker/docker-compose.yml restart overseer-api`

### Monitor não recolhe dados

1. Verificar configuração de triggers em `runtime/triggers/`
2. Verificar conectividade com pipelines externos
3. Verificar credenciais de API (`OVERSEER_API_TOKEN`)

### Base de dados cheia

1. Executar retenção: `python scripts/overseer_retention.py --dry-run`
2. Aplicar após revisão: `python scripts/overseer_retention.py --apply`
3. Considerar archive de runs antigos

## Procedimentos de Emergência

### Rollback de Deployment

Restaurar checkout, imagem e `.env` do snapshot pré-deploy. Não remover volumes.

```bash
docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
```

### Parar Tudo

```bash
docker compose --project-directory . -f docker/docker-compose.yml down
```

### Limpar Volumes

```bash
docker compose --project-directory . -f docker/docker-compose.yml down -v  # CUIDADO: apaga dados
```
