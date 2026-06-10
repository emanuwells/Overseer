# RUNBOOK.md

Guia operacional para deploy, produção, logs, rollback e incidentes.

## Quando Usar

Usar quando houver:

- produção;
- VPS;
- SSH;
- Docker;
- Coolify/Portainer;
- deploy;
- jobs/workers;
- bases de dados;
- incidentes.

## Diagnóstico Rápido

```bash
pwd
git status --short
git branch --show-current
git remote -v
docker compose ps
docker compose logs -f
```

## Antes De Deploy

```text
[ ] Ambiente confirmado.
[ ] Branch confirmada.
[ ] Alterações locais verificadas.
[ ] Dependências instaláveis.
[ ] Build/testes passam.
[ ] Backup/rollback considerado.
[ ] Comandos documentados em COMMANDS.md.
```

## Rollback

Documentar por projeto:

```text
- versão anterior;
- comando de rollback;
- backup necessário;
- migrations reversíveis;
- volumes afetados;
- riscos.
```

## Comandos Críticos

Não executar sem confirmação:

```bash
docker compose down -v
git reset --hard
git clean -fd
rm -rf
DROP DATABASE
systemctl restart
reboot
```
