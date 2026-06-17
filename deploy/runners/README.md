# Catálogos de runners por host

Cada máquina tem um ficheiro **`deploy/runners/<host>.yaml`**, onde `<host>` é o
hostname normalizado da máquina (ex.: `baze2.yaml`, `HP-Z2-EF.yaml`).

## Resolução automática

Os scripts `provision-runners.sh` / `provision-runners.ps1` (sem `-Catalog`)
procuram o catálogo nesta ordem:

1. `--catalog` / `-Catalog` explícito
2. Variável `OVERSEER_RUNNERS_CATALOG`
3. `OVERSEER_HOST_ID` em `~/overseer-runners/.env.overseer` (ou `%USERPROFILE%\...`)
4. `hostname` da máquina

Ficheiros com prefixo `_` (ex.: `_example.yaml`, `_medidata.yaml`) são
**templates** e não são auto-detectados.

## Ficheiros neste repo

| Ficheiro | Host | Uso |
|----------|------|-----|
| `baze2.yaml` | Servidor prod Linux | Pipelines D4MAIA |
| `WS1207.yaml` | Máquina Medidata Windows | Pipeline Medidata (`host_id=WS1207`, Task Scheduler) |
| `_medidata.yaml` | Template | Copiar para `<hostname>.yaml` na máquina Medidata |
| `_example.yaml` | Template | Exemplo genérico Windows |

Após atualizar o repo na WS1207, reinstalar o agente e reprovisionar antes de analisar runs:

```powershell
.\scripts\windows\install-runner.ps1 -RepoPath C:\MAIATRON\Overseer -SshTarget eferreira@195.23.9.32
.\scripts\windows\provision-runners.ps1 -Register
```

## Nova máquina Windows

```powershell
# Ver o nome esperado do catálogo
.\scripts\windows\show-host-catalog.ps1

# Criar deploy/runners/<hostname>.yaml a partir do template Medidata
.\scripts\windows\new-host-catalog.ps1 -Template _medidata.yaml

# Commit + push do novo ficheiro, depois:
.\scripts\windows\provision-runners.ps1 -Register
```

## Run now via API (Ambiente MAIATRON)

Com `OVERSEER_SSH_SYNC_ENABLED=1` na API (baze2), o botão **Run now** envia
`POST /v1/orchestrate/triggers` com `host_id`. A API faz SSH ao worker e arranca
`~/overseer-runners/<pipeline_id>/run.sh` (Linux) ou `run.ps1` (Windows) em background.

Pipelines podem ser **suspensos** com `PATCH` e `suspended: true` sem alterar
o schedule. O Medidata (`WS1207`) tem schedule diário `30 7 * * *`; se passar
mais de 24h sem run, deve aparecer como `stale`.

## Alterar pipelines (já migrado)

Só re-provisionar — **não** mexer no Task Scheduler nem no crontab:

```bash
bash scripts/provision-runners.sh --register          # Linux
```

```powershell
.\scripts\windows\provision-runners.ps1 -Register     # Windows
```

Migrar Scheduler/crontab só na **primeira vez** por pipeline.
