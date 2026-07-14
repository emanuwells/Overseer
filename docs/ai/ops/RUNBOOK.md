# Runbook

## Visão Geral

Este documento contém procedimentos operacionais para o Overseer.

## Ambiente

- **Produção**: Docker-first, auto-hosteado
- **Desenvolvimento**: Docker Compose local
- **Base de Dados**: PostgreSQL

## Comandos Essenciais

Ver `COMMANDS.md` para lista completa.

### Startup

```bash
# Local
docker compose --project-directory . -f docker/docker-compose.yml up -d

# Produção
docker compose --project-directory . -f docker/docker-compose.prod.yml up -d
```

### Logs

```bash
docker compose --project-directory . -f docker/docker-compose.yml logs -f overseer-api
```

### Restore

```bash
docker-compose exec -T postgres psql -U overseer < backup.sql
```

## Monitorização

- Health check: `GET /health`
- Métricas: `GET /metrics`
- Dashboard: `frontend/`

## Troubleshooting

### API não responde

1. Verificar logs: `docker-compose logs overseer-api`
2. Verificar DB: `docker-compose exec postgres psql -U overseer -c "SELECT 1"`
3. Reiniciar: `docker-compose restart overseer-api`

### Monitor não recolhe dados

1. Verificar configuração de triggers em `runtime/triggers/`
2. Verificar conectividade com pipelines externos
3. Verificar credenciais de API

### Base de dados cheia

1. Executar retenção: `python scripts/overseer_retention.py`
2. Verificar políticas de retenção
3. Considerar archive de runs antigos

## Procedimentos de Emergência

### Rollback de Deployment

```bash
docker-compose pull
docker-compose up -d
```

### Parar Tudo

```bash
docker-compose down
```

### Limpar Volumes

```bash
docker-compose down -v  # CUIDADO: apaga dados