# Integração Padrão De Pipelines No Overseer

Este é o contrato para ligar qualquer repositório de pipeline ao Overseer sem copiar o código do pipeline para este repositório.

## Princípio

O pipeline não escreve diretamente na base de dados. O pipeline comunica sempre por API:

- catálogo DAG: `/v1/catalog/pipelines`;
- run: `/v1/events/runs/start` e `/v1/events/runs/{run_id}/finish`;
- módulo: `/v1/events/modules`;
- log/evento: `/v1/events/logs`;
- heartbeat: `/v1/events/heartbeat`;
- triggers operacionais: `/v1/orchestrate/triggers`.

## Instalação Em Cada Repo De Pipeline

Copiar o template:

```text
docs/resources/examples/overseer/pipeline-repo/
```

Para a raiz do repo do pipeline:

```text
pipeline-repo/
  .env.overseer.example
  requirements-overseer.txt
  overseer_bootstrap.py
  src/main.py
```

Depois:

```bash
python -m pip install -r requirements-overseer.txt
```

Criar `.env.overseer` a partir de `.env.overseer.example` e preencher:

```env
OVERSEER_API_URL=http://127.0.0.1:8090
OVERSEER_API_TOKEN=change-me-api-token
OVERSEER_PIPELINE_ID=my_pipeline
OVERSEER_PIPELINE_NAME=My Pipeline
OVERSEER_PIPELINE_OWNER=data
OVERSEER_PIPELINE_CRITICALITY=medium
OVERSEER_PIPELINE_SCHEDULE=manual
```

Nunca guardar `.env.overseer` com credenciais reais no Git.

## Registo Do DAG

```python
from overseer_bootstrap import overseer

overseer.register_catalog(
    nodes=[
        {"module_id": "extract", "label": "Extrair", "type": "task"},
        {"module_id": "transform", "label": "Transformar", "type": "task"},
        {"module_id": "load", "label": "Carregar", "type": "task"},
    ],
    edges=[
        {"from_module_id": "extract", "to_module_id": "transform"},
        {"from_module_id": "transform", "to_module_id": "load"},
    ],
)
```

O registo é idempotente por `pipeline_id`: cada novo envio atualiza os dados do pipeline, substitui nodes e substitui edges desse pipeline.

## Instrumentação

```python
from overseer_bootstrap import overseer

with overseer.run() as run_id:
    with overseer.step(run_id, "extract"):
        overseer.log(run_id, "Dados extraídos.", module_id="extract")

    with overseer.step(run_id, "transform"):
        overseer.log(run_id, "Transformação concluída.", module_id="transform")

    with overseer.step(run_id, "load"):
        overseer.log(run_id, "Carga concluída.", module_id="load")
```

Também é possível envolver um comando inteiro a partir do repo do pipeline:

```bash
python -m overseer_agent exec --pipeline my_pipeline -- python src/main.py
```

## Observabilidade Por Script Sem Alterar O Código (Manifest)

Quando não se quer instrumentar o código do pipeline, descreve-se o pipeline num
manifest YAML fora do repo (por exemplo em `~/overseer-runners/<pipeline_id>/manifest.yaml`).
Cada passo vira um módulo no Overseer, com stdout/stderr e estado `ok`/`failed`.

```yaml
pipeline_id: forms_to_lake
pipeline_name: Forms to Lake
steps:
  - module_id: extract
    command: ["python3", "/caminho/extract.py"]
  - module_id: load
    command: ["python3", "/caminho/load.py"]
```

Registar o DAG (uma vez) e correr:

```bash
overseer-agent manifest ~/overseer-runners/forms_to_lake/manifest.yaml --register-catalog
overseer-agent manifest ~/overseer-runners/forms_to_lake/manifest.yaml --by cron
```

O modelo completo está em `docs/resources/examples/overseer/runner/`. A primeira falha de um passo
crítico interrompe a run; um passo com `critical: false` é marcado mas não
interrompe.

## Windows, Task Scheduler E Multi-host

Pipelines em Windows seguem o mesmo contrato, mas usam `run.ps1` e o Task
Scheduler em vez de `run.sh` e crontab. A máquina Windows não liga à base de
dados: liga à API por túnel SSH em loopback (porta local `18090` ->
`127.0.0.1:8090` no servidor de prod), por isso `OVERSEER_API_URL` é
`http://127.0.0.1:18090`.

O modelo está em `docs/resources/examples/overseer/runner-windows/`. O onboarding completo de uma
máquina é um único comando, que instala o agente, gera o `.env.overseer`
automaticamente (URL, host_id e token via SSH do prod) e regista o túnel SSH +
heartbeat:

```powershell
# Pré-requisito: SSH por chave (sem password) para o prod, com
# ~/overseer-runners/.env.overseer já existente lá (contém o token).
.\scripts\windows\bootstrap-windows.ps1 -RepoPath "C:\Dev\Repos\your-organization\Overseer" -SshTarget operator@server.example.com
```

Depois, por cada conjunto de pipelines (catálogo `$OVERSEER_RUNNERS_DIR/<hostname>.yaml`):

```powershell
# Ver o nome do catálogo esperado nesta máquina
.\scripts\windows\show-host-catalog.ps1

# Se ainda não existir no repo (ex. Forms ou Example):
.\scripts\windows\new-host-catalog.ps1 -Template _example.yaml

# Setup completo: provision + Task Scheduler + heartbeat (conta não admin)
.\scripts\windows\setup-pipeline-windows.ps1 -PipelineId windows_pipeline -TestRun

# Guia passo a passo: docs/windows-pipeline-onboarding.md
```

Alternativa granular:

```powershell
.\scripts\windows\provision-runners.ps1 -Register
.\scripts\windows\register-pipeline-task.ps1 -PipelineId windows_pipeline

# Só se existirem tarefas legadas que chamam o .py directamente:
.\scripts\windows\migrate-taskscheduler.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
```

Num servidor Linux, o catálogo privado segue o formato `$OVERSEER_RUNNERS_DIR/<host-id>.yaml`:

```bash
bash scripts/provision-runners.sh --register
```

### Configuração Automática (.env.overseer)

`bootstrap-windows.ps1` (ou `Initialize-OverseerEnv.ps1` à parte) preenche o
`.env.overseer` sem intervenção manual:

- `OVERSEER_API_URL` -> `http://127.0.0.1:18090` (porta do túnel).
- `OVERSEER_HOST_ID` -> hostname local normalizado.
- `OVERSEER_API_TOKEN` -> lido por SSH de `~/overseer-runners/.env.overseer` no
  prod (ou passado em `-ApiToken`).

O ficheiro fica com ACL restrita ao utilizador e nunca é versionado.

### Convenção Multi-host

Quando o mesmo pipeline lógico corre em várias máquinas, o `pipeline_id`
efetivo recebe o sufixo do host: `{id}__{host_id}` (ex.: `forms_sync__WIN-ETL01`).
O `host_id` vem de `OVERSEER_HOST_ID` no `.env.overseer` (ou do hostname
normalizado) e é enviado em todos os eventos de API. O `pipeline_id` mantém-se
lógico e partilhado; o DAG (`nodes`/`edges`) é único por pipeline. Deployments
distintos (linux-host, windows-host, …) diferenciam-se pela coluna `host_id`.

Runners Windows atrás de proxy: o SDK ignora variáveis `HTTP_PROXY` (`trust_env=False`);
os scripts `run.ps1` e `heartbeat.ps1` limpam proxy para `127.0.0.1`.

### Observabilidade Sempre Ligada

Duas tarefas de infraestrutura garantem visibilidade contínua:

- **Overseer SSH Tunnel** (`At logon`, reinicia se cair): mantém o canal para a API.
- **Overseer Heartbeat** (cada 5 min): envia `heartbeat` com `api_reachable`. Se
  o túnel ou a API caírem, o heartbeat fica `degraded`, visível no painel
  Ambiente do frontend.

O heartbeat Windows também tenta recolher inventário read-only do Task Scheduler
antes de contactar a API. O script `scripts/windows/collect-taskscheduler-info.ps1`
lê `%USERPROFILE%\overseer-runners\catalog.json`, procura as tasks por
`task_name`, `run_ps` ou `task_match`, e anexa o resumo em
`payload.task_scheduler`. A recolha inclui estado, ações, triggers, última
execução, próxima execução e último resultado. Se a recolha falhar, o heartbeat
continua a ser enviado com `task_scheduler.ok=false` e uma mensagem curta de
erro.

Validação local na máquina Windows:

```powershell
.\scripts\windows\collect-taskscheduler-info.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
.\scripts\windows\heartbeat.ps1
```

Validação na API:

```text
GET /v1/read/heartbeats?limit=1
```

O frontend, em `Ambiente > Task Scheduler`, mostra o último inventário recebido
por host e o detalhe read-only por pipeline. Não existem ações de execução,
criação ou alteração de scheduled tasks nesse fluxo.

## Validação De Fluxo

Com o Overseer arrancado:

```bash
docker compose exec overseer-api python scripts/overseer_emit_demo.py
```

Depois abrir:

```text
http://127.0.0.1:8090/ui/dashboard.html
```

## DB Oficial

Para ligar o Overseer ao schema oficial:

1. Copiar `.env.official.example` para `.env`.
2. Preencher `OVERSEER_DB_URL` com a ligação real ao schema `Overseer`.
3. Reiniciar:

```bash
docker compose up -d
```

4. Confirmar no frontend, em `Ambiente`, que a base de dados está acessível.
