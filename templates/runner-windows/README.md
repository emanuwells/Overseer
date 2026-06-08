# Runner Overseer Por Manifest (Windows)

Este modelo liga pipelines Windows ao Overseer central **sem alterar o código** dos
seus repositórios. Em vez de instrumentar cada script, descreve-se o pipeline num
manifest YAML que vive fora do repo, e um runner executa os passos reportando
telemetria por API. É o equivalente Windows de [`templates/runner/`](../runner/README.md).

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
  forms_to_lake__WIN-ETL01\
    manifest.yaml
    run.ps1
    run.log                           # opcional: redirect do Task Scheduler
```

O sufixo `__<host_id>` no nome da pasta e no `pipeline_id` evita colisões quando o
mesmo pipeline lógico corre em várias máquinas.

## Instalação

A forma mais simples é um único comando que instala o agente, gera o
`.env.overseer` automaticamente (URL, host_id e token via SSH do prod) e regista
o túnel SSH + heartbeat no Task Scheduler:

```powershell
.\scripts\windows\bootstrap-windows.ps1 -RepoPath "C:\Dev\Repos\emanuwells\Overseer" -SshTarget eferreira@195.23.9.32
```

Pré-requisito: SSH por chave (sem password) para o servidor de prod, com
`~/overseer-runners/.env.overseer` já existente lá (contém o token).

Em alternativa, por passos:

1. Instalar o agente num venv local (Python 3.11+):

```powershell
.\scripts\windows\install-runner.ps1 -RepoPath "C:\Dev\Repos\emanuwells\Overseer" -SshTarget eferreira@195.23.9.32
```

   Com `-SshTarget`, o `.env.overseer` é gerado automaticamente. Sem ele,
   correr depois `Initialize-OverseerEnv.ps1` ou preencher à mão a partir de
   `.env.overseer.example`.

2. Manter o túnel SSH e o heartbeat sempre ligados:

```powershell
.\scripts\windows\register-infra-tasks.ps1 -SshTarget eferreira@195.23.9.32
```

3. Catálogo por host em `deploy/runners/<hostname>.yaml` (ver
   `deploy/runners/README.md`). Na máquina Medidata:

```powershell
.\scripts\windows\show-host-catalog.ps1
.\scripts\windows\new-host-catalog.ps1 -Template _medidata.yaml
.\scripts\windows\provision-runners.ps1 -Register
```

4. Registar o DAG uma vez (o `--register` acima já o faz; manualmente):

```powershell
$venv = Join-Path $env:LOCALAPPDATA "overseer-venv"
& "$venv\Scripts\overseer-agent.exe" manifest "$env:USERPROFILE\overseer-runners\forms_to_lake__WIN-ETL01\manifest.yaml" --register-catalog --catalog-only
```

5. Apontar o Task Scheduler para o `run.ps1` (ver `migrate-taskscheduler.ps1`).

## Validação

```powershell
& "$env:USERPROFILE\overseer-runners\forms_to_lake__WIN-ETL01\run.ps1"
```

Depois confirmar a run, os módulos e os heartbeats no frontend central.
