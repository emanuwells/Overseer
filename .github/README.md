# Automação GitHub

O baseline WELLS 1.3.0 está aplicado ao layout real do Overseer:

- `workflows/ci.yml`: testes Python, auditoria/build frontend e validação/build Docker;
- `dependabot.yml`: GitHub Actions, npm (`/frontend`), pip (`/src`) e Docker (`/docker`).

O workflow genérico `wells-runtime.yml` não é aplicável neste repositório porque o runtime
`.agents/` é local e está deliberadamente fora do Git. A CI usa ações fixadas por SHA,
permissão mínima de leitura, timeouts e cancelamento de execuções obsoletas.

Nas definições nativas do GitHub devem permanecer ativos o secret scanning/push protection,
o CodeQL default setup e a proteção de `main`. Os checks a exigir no ruleset são:

- `Backend / tests`;
- `Frontend / build`;
- `Docker / build`.
