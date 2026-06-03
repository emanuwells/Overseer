# Todo

## Plano Atual

- [x] Ler `AGENTS.md` e aplicar proporcionalidade de tarefa nao trivial.
- [x] Verificar estado Git e preservar alteracoes existentes.
- [x] Ler `HANDOFF.md`, `SKILLS.md`, Skills relevantes, `CHANGELOG_POLICY.md`, topo de `CHANGELOG.md`, `README.md` e `PROJECT_CONTEXT.template.md`.
- [x] Verificar configuracoes MCP no repositorio.
- [x] Criar `PROJECT_CONTEXT.md` com informacao confirmada.
- [x] Atualizar `README.md` com badges, arquitetura, estrutura real, Docker avaliado e politica de segredos.
- [x] Validar comandos/testes aplicaveis.
- [x] Atualizar `HANDOFF.md`.
- [x] Atualizar `CHANGELOG.md`.

## Validação

- [x] `git status --short --branch` executado.
- [x] `python orchestrator.py --help` tentou validar CLI.
- [x] `python -m compileall orchestrator.py overseer_monitor overseer_sdk scripts src pipelines` passou.
- [x] `python orchestrator.py --help` falhou por dependencia `PyYAML` ausente no Python ativo.

## Revisão Final

- [x] Auditar ficheiros desnecessarios.
- [x] Confirmar ausencia da credencial removida no `README.md`.
- [x] Aplicar checklist final de `definition-of-done`.
