# Arquitetura Frontend

## Responsabilidade

O frontend do Overseer é uma SPA React read-only para observar estado operacional. A interface não é a fonte de verdade para alterações de catálogo, execução ou sync remoto; essas operações são feitas por API, CLI ou scripts operacionais.

## Stack

| Tecnologia | Finalidade |
|---|---|
| React 19 | componentes e estado de UI |
| TypeScript | tipos e contratos internos |
| Vite 6 | build e dev server |
| React Router 7 | rotas client-side |
| TanStack Query 5 | cache e fetching da API |
| Tailwind CSS 4 | estilos utilitários e tema escuro |

## Estrutura

| Área | Localização | Responsabilidade |
|---|---|---|
| Entry | `frontend/index.html`, `frontend/src/main.tsx` | bootstrap da SPA |
| Rotas | `frontend/src/App.tsx` | `/operations`, `/runs`, `/dag`, `/environment` |
| Layout | `frontend/src/components/layout/` | sidebar, topbar, breadcrumbs |
| Páginas | `frontend/src/pages/` | vistas operacionais |
| API | `frontend/src/lib/api.ts`, `frontend/src/lib/utils.ts` | cliente HTTP e helpers |
| Config | `frontend/public/overseer-config.example.js` | exemplo de token (produção via deploy) |
| Build | `frontend/dist/` (`/ui/`) ou `frontend/dist-nginx/` (`/Overseer/`) |

## Rotas

| Rota | Vista |
|---|---|
| `/ui/` | redireciona para operações |
| `/ui/operations` | dashboard e KPIs |
| `/ui/runs` | histórico e detalhe de runs |
| `/ui/dag` | catálogo DAG e módulos |
| `/ui/environment` | base de dados, hosts, heartbeats, triggers |

Deep links: `/ui/runs?run=…&pipeline=…&host=…`, `/ui/dag?pipeline=…&host=…`.

## Integração API

- A UI consome principalmente endpoints `/v1/read/*`.
- Tokens via `window.OVERSEER_CONFIG.apiToken` ou `sessionStorage`.
- A UI não deve expor segredos reais nem incorporar credenciais versionadas.
- Erros de API apresentados como estados de leitura, sem alterar dados.

## Entrega

- Desenvolvimento: `scripts/dev-ui.ps1` (Docker) ou `scripts/dev-frontend.ps1` (Vite).
- Produção nginx: `npm run build:nginx` → `/Overseer/`; `scripts/deploy-nginx-frontend.sh`.
- Fallback SPA: rotas desconhecidas sob `/ui/` devolvem `index.html`.

## Regras de evolução

- Preservar o caráter read-only salvo decisão arquitetural explícita.
- Justificar novas dependências npm (benefício vs custo de build e segurança).
- Validar com `npm run build`, browser ou teste manual após alterações visuais.
- Manter textos em português europeu quando forem conteúdo controlado pelo projeto.
