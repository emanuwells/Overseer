# Pipeline Template — Overseer

Este diretório é o ponto de partida canónico para criar um **novo pipeline** no Overseer.

## Como usar

```bash
# 1. Copiar a template
cp -r pipelines/_template pipelines/meu_novo_pipeline

# 2. Adaptar os ficheiros
#    - pipeline.yaml         → definir pipeline_id, schedule, owner, etc.
#    - config/monitoring.json → copiar do .example e ajustar
#    - secrets/database.json  → copiar do .example e preencher credenciais
#    - secrets/slack.json     → copiar do .example e preencher webhook
#    - src/main.py            → implementar a lógica de negócio

# 3. Verificar que o pipeline aparece no orchestrator
python orchestrator.py list

# 4. Testar manualmente
python orchestrator.py run meu_novo_pipeline

# 5. Exportar payload para frontend
python scripts/export_payload_from_db.py
```

## Estrutura obrigatória

```
pipelines/meu_novo_pipeline/
├── pipeline.yaml                # Contrato YAML (obrigatório)
├── config/
│   ├── monitoring.json          # Config de monitorização (obrigatório)
│   └── monitoring.json.example  # Placeholder para git
├── secrets/
│   ├── .gitkeep
│   ├── database.json            # Credenciais BD (gitignored)
│   ├── database.json.example    # Placeholder
│   ├── slack.json               # Config Slack (gitignored)
│   ├── slack.json.example       # Placeholder
│   └── ssh_key                  # Chave SSH (gitignored, se necessário)
└── src/
    ├── main.py                  # Entry point (obrigatório)
    └── ...                      # Módulos do pipeline
```

## Contrato de pipeline.yaml

Campos obrigatórios:

| Campo              | Descrição                                       |
|--------------------|------------------------------------------------|
| `pipeline_id`      | ID único (snake_case, sem espaços)             |
| `name`             | Nome legível para o frontend                   |
| `owner`            | Username do responsável                        |
| `criticality`      | `low` / `medium` / `high` / `critical`         |
| `runner_host`      | `auto` (local), `any` (qualquer), ou hostname  |
| `schedule`         | Expressão cron, `manual`, ou `paused`          |
| `timeout_sec`      | Timeout máximo em segundos                     |
| `retries`          | Número de retentativas em caso de falha        |
| `entrypoint`       | Comando Linux (ex: `python src/main.py`)       |
| `entrypoint_windows`| Comando Windows (ex: `python src\main.py`)   |

## Padrão standard do main.py

Todos os pipelines devem seguir o mesmo padrão:

1. **Imports SDK**: `RuntimeContext`, `get_logger`, `SSHTunnelManager`, `SlackNotifier`
2. **LineageEmitter**: emitir markers para CADA fase (`config_loading`, `infrastructure`, `processing`, `slack_notification`)
3. **OverseerMonitor**: usar **apenas em modo standalone** (quando `runtime_ctx.orchestrator_managed == False`). O orchestrator já gere `pipeline_runs`.
4. **Slack**: notificar no `finally` (obrigatório)
5. **Cleanup**: libertar SSH tunnel e DB no `finally`

## Portabilidade entre máquinas

O pipeline funciona em qualquer máquina graças a:

- **RuntimeContext**: deteta automaticamente se a BD é local ou remota
- **SSHTunnelManager**: cria SSH tunnel quando a BD é remota
- **secrets/database.json**: cada máquina tem as suas credenciais (gitignored)
- **runner_host** no pipeline.yaml: `auto` = hostname local, `any` = qualquer runner

### Setup numa nova máquina

1. Clonar o repositório
2. Copiar `secrets/*.example` para `secrets/*` (sem .example) e preencher
3. Copiar a SSH key para `secrets/ssh_key` (se BD remota)
4. `pip install -r requirements.txt`
5. `python orchestrator.py list` para verificar
6. `python orchestrator.py run <pipeline_id>` para testar
