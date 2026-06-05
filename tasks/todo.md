# Todo

## Plano Atual — 4.2.1

- [x] Preservar o template visual colocado em `frontend/`.
- [x] Adaptar `dashboard.html` para dados reais de overview/database.
- [x] Adaptar `run-detail.html` para run mais recente, módulos e logs.
- [x] Adaptar `lineage.html` para catálogo DAG real.
- [x] Adaptar `deployments.html` para DB, heartbeats e triggers.
- [x] Manter `index.html` sem página inicial, redirecionando para dashboard.
- [x] Validar JS, testes, Docker build, Compose e HTTP das páginas.

## Plano Atual — 4.2.0

- [x] Remover página inicial/landing e abrir a UI diretamente em `/ui/dashboard.html`.
- [x] Servir `frontend/` estático pela FastAPI em `/ui/`.
- [x] Substituir dados fictícios do frontend por chamadas a `/v1/read/*`.
- [x] Adicionar `POST /v1/catalog/pipelines` para registo idempotente de catálogo DAG.
- [x] Adicionar `GET /v1/read/pipelines/{pipeline_id}/dag`.
- [x] Criar persistência de nodes e edges em `overseer_pipeline_nodes` e `overseer_pipeline_edges`.
- [x] Remover endpoint de execução local `/v1/orchestrate/pipelines/{pipeline_id}/run`.
- [x] Remover o pipeline exemplo `pipelines/microsoft_forms_2_datalake`.
- [x] Simplificar Dockerfile para runtime Python sem build Node/Vite.
- [x] Remover mount `./pipelines` do Compose.
- [x] Atualizar template externo de pipeline para registo DAG por API.
- [x] Atualizar README, PROJECT_CONTEXT, ADR, OpenAPI, changelog e handoff.

## Decisões Confirmadas

- [x] O Overseer observa pipelines externos por API e não executa o seu código.
- [x] Registo por API é a fonte principal do catálogo; YAML não é obrigatório.
- [x] Triggers são sinais operacionais, não execução local.
- [x] Frontend é HTML/CSS/JS estático servido pela FastAPI.
- [x] Docker continua a ser o fluxo principal.

## Validação

- [x] `git status --short --branch` executado antes das alterações.
- [x] `python -m pytest -q` executado durante a implementação; falhou inicialmente por schema não inicializado nos testes novos.
- [x] Testes ajustados para inicializar schema em DB temporária.
- [x] `python -m pytest -q` final.
- [x] `docker compose config`.
- [x] `docker compose build`.
- [x] `docker compose up -d`.
- [x] Verificação HTTP/API final com health, dashboard, overview, database e DAG demo.

## Revisão Final

- [x] Auditar referências legadas a `webapp`, React/Vite, YAML obrigatório e pipeline exemplo.
- [x] Auditar segredos.
- [x] Aplicar checklist final de `definition-of-done`.
