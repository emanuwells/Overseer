# Runner Overseer Por Manifest (Windows)

Este modelo liga pipelines Windows ao Overseer central **sem alterar o código** dos
seus repositórios. Em vez de instrumentar cada script, descreve-se o pipeline num
manifest YAML que vive fora do repo, e um runner executa os passos reportando
telemetria por API. É o equivalente Windows de [`runner/`](../runner/README.md).

## Princípio

- O repo do pipeline fica intacto (zero ficheiros Overseer).
- O manifest e o wrapper vivem em `%USERPROFILE%\overseer-runners\<pipeline_id>\`.
- Cada passo do manifest vira um módulo no Overseer, com stdout/stderr e estado.
- A primeira falha de um passo crítico interrompe a run.
- A máquina Windows **não liga à base de dados**: liga à API por **túnel SSH** em
  loopback (porta local `18090` -> `127.0.0.1:8090` no servidor de prod).

## Estrutura No Host

```text
%USERPROFILE%\overseer-runners\
  .env.overseer                       # OVERSEER_API_URL + token + OVERSEER_HOST_ID (partilhado)
  example_pipeline\
    manifest.yaml                     # pipeline_id lógico + metadata.host_id
    run.ps1
    run.log                           # opcional: redirect do Task Scheduler
```

O `pipeline_id` no manifest é lógico (ex. `example_pipeline`); o deployment por
máquina distingue-se pela coluna `host_id` / `metadata.host_id` / `OVERSEER_HOST_ID`.

Em redes com proxy corporativo, os wrappers definem `NO_PROXY=127.0.0.1,localhost`
e o SDK usa `httpx` com `trust_env=False` para o túnel SSH em loopback.

## Instalação

A forma mais simples é um único comando que instala o agente, gera o
`.env.overseer` automaticamente (URL, host_id e token via SSH do prod) e regista
o túnel SSH + heartbeat no Task Scheduler:

```powershell
.\scripts\windows\bootstrap-windows.ps1 -RepoPath "C:\Dev\Repos\your-organization\Overseer" -SshTarget operator@server.example.com
```

Pré-requisito: SSH por chave (sem password) para o servidor de prod, com
`~/overseer-runners/.env.overseer` já existente lá (contém o token).

Em alternativa, por passos:

1. Instalar o agente num venv local (Python 3.11+):

```powershell
.\scripts\windows\install-runner.ps1 -RepoPath "C:\Dev\Repos\your-organization\Overseer" -SshTarget operator@server.example.com
```

   Com `-SshTarget`, o `.env.overseer` é gerado automaticamente. Sem ele,
   correr depois `Initialize-OverseerEnv.ps1` ou preencher à mão a partir de
   `.env.overseer.example`.

2. Manter o túnel SSH e o heartbeat sempre ligados:

```powershell
.\scripts\windows\register-infra-tasks.ps1 -SshTarget operator@server.example.com
```

3. Catálogo privado por host em `$OVERSEER_RUNNERS_DIR/<hostname>.yaml` (ver
   `deploy/runners/README.md`). Na máquina Example:

```powershell
.\scripts\windows\show-host-catalog.ps1
.\scripts\windows\new-host-catalog.ps1 -Template _example.yaml
.\scripts\windows\provision-runners.ps1 -Register
```

4. Registar o DAG uma vez (o `--register` acima já o faz; manualmente):

```powershell
$venv = Join-Path $env:LOCALAPPDATA "overseer-venv"
& "$venv\Scripts\overseer-agent.exe" manifest "$env:USERPROFILE\overseer-runners\forms_to_lake__WIN-ETL01\manifest.yaml" --register-catalog --catalog-only
```

5. Apontar o Task Scheduler para o `run.ps1` (ver `migrate-taskscheduler.ps1`).

## Heartbeat E Inventário Task Scheduler

O `heartbeat.ps1` envia o heartbeat normal do agente e, antes disso, tenta
recolher inventário read-only do Task Scheduler através de
`collect-taskscheduler-info.ps1`. A recolha usa
`%USERPROFILE%\overseer-runners\catalog.json` e procura cada pipeline por
`task_name`, `run_ps` ou `task_match`.

O payload enviado para `/v1/events/heartbeat` mantém `agent_version` e
`api_reachable`, e acrescenta `payload.task_scheduler` com:

- `ok`, `collected_at` e `host_id`;
- pipeline observado, task encontrada, estado, próxima execução e último
  resultado;
- ações e triggers configurados;
- `task_found=false` quando não há correspondência.

Se o inventário falhar, o heartbeat não é bloqueado: o payload segue com
`task_scheduler.ok=false` e uma mensagem curta em `error`.

## Validação

```powershell
& "$env:USERPROFILE\overseer-runners\forms_to_lake__WIN-ETL01\run.ps1"
.\scripts\windows\collect-taskscheduler-info.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
.\scripts\windows\heartbeat.ps1
```

Depois confirmar a run, os módulos, os heartbeats e o separador
`Ambiente > Task Scheduler` no frontend central.
