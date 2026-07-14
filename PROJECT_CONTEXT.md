# Contexto do projeto

O Overseer é um serviço de observabilidade para pipelines externos. A API recebe catálogo e telemetria, a camada de persistência mantém o estado operacional e a interface web expõe consultas read-only.

## Stack

| Área | Tecnologia |
|---|---|
| API | FastAPI e Uvicorn |
| Persistência | SQLAlchemy; MariaDB no Compose oficial |
| SDK e agente | Python e HTTPX |
| Interface | HTML, CSS e JavaScript estático |
| Operação | Docker Compose e scripts multiplataforma |
| Testes | pytest |

## Limites

- O núcleo não contém o código dos pipelines observados.
- Catálogos e credenciais reais não pertencem ao repositório.
- A interface web não altera catálogo, agendas nem execuções.
- A API pública mantém contratos versionados sob `/v1`.

## Configuração operacional

`OVERSEER_RUNNERS_DIR` aponta para um diretório privado com `hosts.yaml` e um catálogo `<host-id>.yaml` por host. O diretório é montado no container em `/app/deploy/runners`.

`OVERSEER_RUNTIME_DIR` mantém estado e ficheiros operacionais fora do checkout, permitindo substituir ou reverter a revisão sem mover dados.

## Verificação

```bash
python -m pytest -q
docker compose --project-directory . -f docker/docker-compose.yml config
docker compose --project-directory . -f docker/docker-compose.yml build
```

Alterações de produção exigem backup verificável, plano de rollback e validação do endpoint `/v1/health`.
