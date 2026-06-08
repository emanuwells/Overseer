# Runner Overseer Por Manifest

Este modelo permite ligar pipelines ao Overseer **sem alterar o código** dos seus
repositórios. Em vez de instrumentar cada script, descreve-se o pipeline num
manifest YAML que vive fora do repo, e um runner executa os passos reportando
telemetria por API.

## Princípio

- O repo do pipeline fica intacto (zero ficheiros Overseer).
- O manifest e o wrapper vivem em `~/overseer-runners/<pipeline_id>/`.
- Cada passo do manifest vira um módulo no Overseer, com stdout/stderr e estado.
- A primeira falha de um passo crítico interrompe a run.

## Estrutura No Host

```text
~/overseer-runners/
  .env.overseer                 # OVERSEER_API_URL + OVERSEER_API_TOKEN (partilhado)
  forms_to_lake/
    manifest.yaml
    run.sh
```

## Instalação

1. Instalar o pacote num venv no host onde os pipelines correm:

```bash
python3 -m venv ~/overseer-venv
~/overseer-venv/bin/pip install -e /home/eferreira/Dev/Repos/emanuwells/Overseer
```

2. Criar a configuração partilhada `~/overseer-runners/.env.overseer` a partir de
   `.env.overseer.example`.

3. Por pipeline, criar a pasta e copiar `pipeline.manifest.yaml.example` para
   `manifest.yaml` e `run.sh.example` para `run.sh`, ajustando comandos e paths.

4. Registar o DAG uma vez:

```bash
source ~/overseer-runners/.env.overseer
~/overseer-venv/bin/overseer-agent manifest ~/overseer-runners/forms_to_lake/manifest.yaml --register-catalog
```

5. Apontar o crontab para o `run.sh` (ver exemplo dentro do ficheiro).

## Validação

```bash
~/overseer-venv/bin/overseer-agent manifest ~/overseer-runners/forms_to_lake/manifest.yaml --by manual
```

Depois confirmar a run e os módulos no frontend.

## Windows

Para máquinas Windows (Task Scheduler + túnel SSH), usar o modelo equivalente em
[`templates/runner-windows/`](../runner-windows/README.md) e os scripts em
`scripts/windows/`. O contrato e a convenção multi-host estão em
[`docs/pipeline-integration.md`](../../docs/pipeline-integration.md).
