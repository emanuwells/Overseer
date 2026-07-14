# Arquitetura Backend

## Responsabilidade

O backend centraliza os contratos HTTP, autenticação opcional por bearer token, validação de payloads, persistência relacional e exposição de leitura operacional. O núcleo recebe sinais de sistemas externos; não executa diretamente pipelines observados.

## Estrutura

| Área | Caminho | Responsabilidade |
|---|---|---|
| Aplicação FastAPI | `src/overseer_api/main.py` | Criação da aplicação, montagem de routers e frontend estático |
| Autenticação | `src/overseer_api/auth.py` | Validação opcional de token API |
| Routers | `src/overseer_api/routers/` | Health, leitura, catálogo, eventos e triggers |
| Domínio | `src/overseer_core/` | Persistência, catálogo, saúde de deployments, Slack e SSH |
| Agent / SDK | `src/overseer_agent/`, `src/overseer_sdk/` | CLI e bibliotecas para emissão de telemetria e operação externa |

## Contratos Principais

- `/v1/health`: estado básico da API.
- `/v1/read/*`: leitura operacional para UI e clientes.
- `/v1/catalog/*`: registo e reconciliação de catálogo de pipelines.
- `/v1/events/*`: ingestão de runs, eventos e heartbeats.
- `/v1/orchestrate/*`: triggers operacionais e dispatch para runners configurados.

## Autenticação E Segurança

- `OVERSEER_API_TOKEN` ativa proteção bearer token quando configurado.
- Segredos reais devem ficar em variáveis de ambiente, gestor de segredos ou ficheiros locais ignorados pelo Git.
- Logs e respostas não devem expor tokens, passwords ou credenciais.

## Regras De Evolução

- Preservar compatibilidade dos endpoints versionados em `/v1`.
- Atualizar `openapi/overseer-api.yaml` quando o contrato API mudar.
- Validar alterações backend com `python -m pytest -q`.
- Não misturar refactor estrutural com mudança funcional sem plano próprio.
