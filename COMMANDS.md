# Comandos

## Desenvolvimento

```bash
pip install -r src/requirements.txt
pip install -e ./src
python -m pytest -q
```

## Frontend

```bash
cd frontend
npm ci
npm run dev
npm run build
```

`npm run dev` arranca Vite com proxy de `/v1` para `http://127.0.0.1:8090`. O build gera `frontend/dist/`, servido pela API em `/ui/`.

## Docker

```bash
docker compose --project-directory . -f docker/docker-compose.yml config
docker compose --project-directory . -f docker/docker-compose.yml up --build -d
docker compose --project-directory . -f docker/docker-compose.yml logs -f overseer-api
docker compose --project-directory . -f docker/docker-compose.yml down
```

Produção requer `.env`, `OVERSEER_DB_URL`, `OVERSEER_RUNNERS_DIR`, `OVERSEER_RUNTIME_DIR` e diretórios privados persistentes:

```bash
docker compose --project-directory . -f docker/docker-compose.prod.yml config
docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d
curl -sf http://127.0.0.1:8090/v1/health
```

## Operações

```bash
overseer-agent trigger <pipeline-id> --host-id <host-id> --by ops
python scripts/overseer_retention.py --dry-run
python scripts/overseer_retention.py --apply
python scripts/maintenance/overseer_db_maintenance.py --pipeline-id <pipeline-id>
```

Utilize `--apply` apenas depois de rever o resultado do modo de simulação. Não execute `docker compose down -v`, purgas, alterações de schema ou operações destrutivas sem backup e confirmação explícita.

## Git e deploy remoto

Os destinos remotos são fornecidos pelo operador e nunca ficam hardcoded:

```bash
ssh <ssh-user>@<server> 'cd <repo-path> && git status --short --branch'
ssh <ssh-user>@<server> 'cd <repo-path> && docker compose --project-directory . -f docker/docker-compose.prod.yml up --build -d'
```
