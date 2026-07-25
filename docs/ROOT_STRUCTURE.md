# Estrutura da Raiz — Overseer

A raiz segue a política de limpeza do toolkit WELLS (`.agents/policies/ROOT_CLEAN_POLICY.md` em ambiente local).

## Raiz esperada

```text
.
├── CHANGELOG.md
├── COMMANDS.md
├── CONTRIBUTING.md
├── LICENSE
├── PROJECT_CONTEXT.md
├── README.md
├── SECURITY.md
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
└── tests/
```

A pasta `.agents/` existe apenas em checkouts com toolkit WELLS instalado e está ignorada pelo Git.

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
