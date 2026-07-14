# Template De Integração Overseer Para Pipelines

Este diretório contém o contrato mínimo para um repositório de pipeline registar o seu DAG e escrever telemetria no Overseer por API.

## Ficheiros

| Ficheiro | Destino No Repo Do Pipeline |
|---|---|
| `.env.overseer.example` | `.env.overseer.example` |
| `requirements-overseer.txt` | `requirements-overseer.txt` |
| `overseer_bootstrap.py` | `overseer_bootstrap.py` |

## Instalação No Repo Do Pipeline

1. Copiar estes ficheiros para a raiz do repo do pipeline.
2. Copiar `.env.overseer.example` para `.env.overseer`.
3. Preencher `OVERSEER_API_URL`, `OVERSEER_API_TOKEN` e `OVERSEER_PIPELINE_ID`.
4. Instalar dependências:

```bash
python -m pip install -r requirements-overseer.txt
```

5. Registar o DAG e instrumentar o script principal:

```python
from overseer_bootstrap import overseer

overseer.register_catalog(
    nodes=[
        {"module_id": "extract", "label": "Extrair"},
        {"module_id": "load", "label": "Carregar"},
    ],
    edges=[
        {"from_module_id": "extract", "to_module_id": "load"},
    ],
)

with overseer.run() as run_id:
    with overseer.step(run_id, "extract"):
        ...
    with overseer.step(run_id, "load"):
        ...
```

## Contrato Operacional

- O catálogo do pipeline é registado em `/v1/catalog/pipelines`.
- Cada execução cria uma run em `/v1/events/runs/start`.
- Cada fase relevante cria um módulo em `/v1/events/modules`.
- Cada evento humano ou técnico escreve em `/v1/events/logs`.
- Cada runner pode enviar heartbeat para `/v1/events/heartbeat`.
