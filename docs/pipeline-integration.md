# Integração Padrão De Pipelines No Overseer

Este é o contrato único para colocar Overseer em qualquer repositório de pipeline.

## Princípio

O pipeline não escreve diretamente na base de dados. O pipeline escreve sempre na API do Overseer:

- run: `/v1/events/runs/start` e `/v1/events/runs/{run_id}/finish`;
- módulo: `/v1/events/modules`;
- log/evento: `/v1/events/logs`;
- heartbeat: `/v1/events/heartbeat`.

## Instalação Em Cada Repo De Pipeline

Copiar o template:

```text
templates/pipeline-repo/
```

Para a raiz do repo do pipeline:

```text
pipeline-repo/
  .env.overseer.example
  pipeline.yaml
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
```

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

## Execução Com Registo Automático

Também é possível envolver um comando inteiro:

```bash
python -m overseer_agent exec --pipeline my_pipeline -- python src/main.py
```

## Validação De Fluxo

Com o Overseer arrancado:

```bash
docker compose exec overseer-api python scripts/overseer_emit_demo.py
```

Depois abrir:

```text
http://127.0.0.1:8090/ui/
```

## DB Oficial

Para ligar o Overseer ao schema oficial:

1. Copiar `.env.official.example` para `.env`.
2. Preencher `OVERSEER_DB_URL` com a ligação real ao schema `Overseer`.
3. Reiniciar:

```bash
docker compose up -d
```

4. Confirmar no frontend, no bloco `Base de dados`, que o modo é `external` e que a database é `Overseer`.

Nunca guardar `.env` ou credenciais reais no Git.
