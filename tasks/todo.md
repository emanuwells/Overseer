# Todo

## Plano Atual

- [x] Refatorar o Overseer para núcleo único com API de leitura, API de escrita e API de orquestração.
- [x] Criar schema novo simples para runs, módulos, logs, heartbeats, pipelines e triggers, mantendo MariaDB como alvo local e SQLAlchemy para preparar outros dialectos.
- [x] Substituir o fluxo legado `DB -> JSON -> MAIATRON` por API HTTP canónica.
- [x] Criar SDK Python e CLI drop-in para instrumentar pipelines por API.
- [x] Criar frontend React/Vite para dashboard local, detalhe, logs, módulos e ações operacionais.
- [x] Atualizar Docker/Compose para workflow único e reprodutível.
- [x] Manter apenas `microsoft_forms_2_datalake` como exemplo de pipeline e remover o restante legado fora de escopo.
- [x] Atualizar `README.md`, `PROJECT_CONTEXT.md`, `CHANGELOG.md` e `HANDOFF.md`.

## Decisões Confirmadas

- [x] O Overseer continua a executar/orquestrar pipelines, mas via API própria.
- [x] Usar uma FastAPI com routers separados, não dois serviços independentes.
- [x] Manter MariaDB/MySQL como base local, preparando o código para outros dialectos como PostgreSQL.
- [x] A API de escrita aceita run, módulos, logs/eventos e heartbeat.
- [x] Fornecer SDK Python e CLI wrapper para pipelines.
- [x] Frontend em React + Vite.
- [x] UI com leitura e ações operacionais.
- [x] Workflow Docker por comando único simples.
- [x] Schema novo simples, sem preservar o legado como contrato principal.
- [x] Remover export JSON/MAIATRON e legado associado.
- [x] Manter apenas `microsoft_forms_2_datalake` como exemplo.
- [x] Autenticação por API token.

## Validação

- [x] `git status --short --branch` executado antes das alterações.
- [x] `python -m pytest -q` passou antes do refactor, com avisos de cache sem permissão.
- [x] Testes de contrato da nova API.
- [x] Build do frontend via `docker compose build`.
- [x] Validação Docker/Compose com build multi-stage.

## Revisão Final

- [x] Auditar segredos e exemplos.
- [x] Auditar ficheiros removidos e candidatos.
- [x] Aplicar checklist final de `definition-of-done`.

## Notas De Validação

- `python -m pytest -q` passou com 4 testes.
- `docker compose build` passou e validou `npm ci`, `vite build` e instalação Python dentro do container.
- `npm install` local em Windows/OneDrive falhou ao escrever `webapp/node_modules`; o fluxo suportado não depende de Node local e `.dockerignore` exclui esse diretório.
