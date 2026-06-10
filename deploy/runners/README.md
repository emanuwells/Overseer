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

Após atualizar o repo (layout `src/`), na WS1207 correr
`scripts\windows\upgrade-windows-runner.ps1 -TestMedidata` antes de analisar runs.
| `_medidata.yaml` | Template | Copiar para `<hostname>.yaml` na máquina Medidata |
| `_example.yaml` | Template | Exemplo genérico Windows |

## Nova máquina Windows

```powershell
# Ver o nome esperado do catálogo
.\scripts\windows\show-host-catalog.ps1

# Criar deploy/runners/<hostname>.yaml a partir do template Medidata
.\scripts\windows\new-host-catalog.ps1 -Template _medidata.yaml

# Commit + push do novo ficheiro, depois:
.\scripts\windows\provision-runners.ps1 -Register
```

## Alterar pipelines (já migrado)

Só re-provisionar — **não** mexer no Task Scheduler nem no crontab:

```bash
bash scripts/provision-runners.sh --register          # Linux
```

```powershell
.\scripts\windows\provision-runners.ps1 -Register     # Windows
```

Migrar Scheduler/crontab só na **primeira vez** por pipeline.
