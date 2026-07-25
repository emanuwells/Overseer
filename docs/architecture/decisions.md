# Decisões Técnicas

Este ficheiro resume decisões arquiteturais vivas. ADRs detalhados continuam em `docs/adr/`.

## Decisões Ativas

| Tema | Decisão | Referência |
|---|---|---|
| Núcleo operacional | O Overseer observa pipelines externos e não executa código de pipelines dentro do núcleo | `docs/adr/0001-overseer-core-api-refactor.md` |
| API | FastAPI única com routers separados para leitura, catálogo, eventos, health e triggers | `docs/adr/0001-overseer-core-api-refactor.md` |
| Persistência | Tabelas `overseer_*` são o contrato persistente ativo | `docs/adr/0001-overseer-core-api-refactor.md` |
| Frontend | UI estática servida em `/ui/`, sem build Node/Vite | `docs/adr/0001-overseer-core-api-refactor.md` |
| Operação | Docker Compose é o fluxo principal para API, UI e MariaDB local | `PROJECT_CONTEXT.md` |
| Governação IA | Toolkit WELLS em `.agents/` (local; ignorado pelo Git) define o fluxo de agentes | Aceite |
| Conformidade IA | Procedimentos e políticas em `.agents/ops/` e `.agents/policies/` | `.agents/state/DECISIONS.md` |

## Regras Para Novas Decisões

- Decisões permanentes ou com impacto arquitetural devem ser registadas em ADR ou neste resumo.
- Mudanças em API, DB, autenticação, Docker, CI/CD, deploy ou execução de pipelines exigem plano próprio.
- Documentação deve seguir o código real quando houver divergência.
