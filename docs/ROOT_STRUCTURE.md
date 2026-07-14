# Estrutura da Raiz — Overseer

A raiz segue o template em `docs/ai/policies/ROOT_CLEAN_POLICY.md`.

## Raiz esperada

```text
.
├── AGENTS.md
├── CHANGELOG.md
├── COMMANDS.md
├── LICENSE
├── PROJECT_CONTEXT.md
├── README.md
├── VERSION
├── .gitattributes
├── .gitignore
├── .github/
├── docker/              # Dockerfile, compose, .dockerignore
├── deploy/              # runners, nginx (sem Docker)
├── docs/
├── frontend/
├── openapi/
├── runtime/
├── scripts/
├── secrets/
├── src/                 # pacotes Python + pyproject.toml + requirements.txt
├── tasks/
├── tests/
└── tools/
```

## Docker

Sempre a partir da raiz do repo:

```bash
docker compose --project-directory . -f docker/docker-compose.yml up --build -d
docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
```

O `Dockerfile` usa `COPY` explícito (não depende de `.dockerignore` na raiz).

## Python local

```bash
pip install -r src/requirements.txt && pip install -e ./src
python -m pytest -q
```
