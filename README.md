# Overseer

![Estado](https://img.shields.io/badge/estado-estável-2ecc71)
![Versão](https://img.shields.io/badge/versão-5.8.26-3498db)
![Licença](https://img.shields.io/badge/licença-proprietária-lightgrey)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)

O Overseer é um serviço Docker-first de observabilidade para pipelines e DAGs externos. Recebe catálogos, runs, eventos e heartbeats por API, persiste o estado operacional e disponibiliza uma interface web de leitura. O núcleo não incorpora nem executa o código dos pipelines observados.

## Funcionalidades

- catálogo de pipelines, nós e dependências;
- ingestão de runs, módulos, logs e heartbeats;
- deteção de deployments inativos ou em risco;
- interface web read-only para consulta operacional;
- SDK e agente Python para integração externa;
- triggers opcionais para runners Linux e Windows;
- alertas e resumos operacionais por Slack.

## Arranque rápido

Requer Docker com Compose.

```bash
cp docs/resources/templates/.env.example .env
docker compose --project-directory . -f docker/docker-compose.yml up --build -d
```

Depois do arranque:

- API: `http://127.0.0.1:8090/v1/health`
- interface: `http://127.0.0.1:8090/ui/dashboard.html`
- OpenAPI: `openapi/overseer-api.yaml`

## Configuração

As opções públicas estão documentadas em `docs/resources/templates/.env.example`. Segredos e configuração operacional devem permanecer fora do Git.

Os catálogos reais de runners são lidos do diretório indicado por `OVERSEER_RUNNERS_DIR`. Em desenvolvimento, a omissão desta variável usa `deploy/runners/`, que contém apenas um exemplo genérico. Em produção, a variável é obrigatória.

Em produção, `OVERSEER_RUNTIME_DIR` deve apontar para armazenamento persistente fora do checkout.

```env
OVERSEER_RUNNERS_DIR=/srv/overseer/runners
```

Consulte [Integração de pipelines](docs/pipeline-integration.md) e [Comandos](COMMANDS.md) para configuração detalhada.

## Desenvolvimento

```bash
pip install -r src/requirements.txt
pip install -e ./src
python -m pytest -q
docker compose --project-directory . -f docker/docker-compose.yml config
```

O backend usa FastAPI e SQLAlchemy. A interface é HTML, CSS e JavaScript estático; não requer Node.js.

## Estrutura

```text
src/        API, domínio, SDK, agente e monitorização
frontend/   interface web estática
docker/     imagem e ficheiros Compose
deploy/     exemplos de configuração operacional
scripts/    arranque, manutenção e provisionamento
tests/      testes automatizados
docs/       arquitetura e integração
```

## Segurança e licença

Consulte [.github/SECURITY.md](.github/SECURITY.md) para comunicar vulnerabilidades. O código é disponibilizado sob licença proprietária; a publicação do repositório não concede direitos adicionais de utilização, modificação ou redistribuição. Consulte [LICENSE](LICENSE).
