# Política de Orçamento de Contexto

## Objetivo

Reduzir ruído, conflitos de instruções e custo cognitivo dos agentes. Mais contexto não significa melhor execução; o agente deve carregar apenas o necessário para a tarefa.

## Regra Principal

O agente deve começar pelo núcleo mínimo e só abrir documentação adicional quando houver relação direta com a tarefa.

## Núcleo Mínimo

Para tarefas não triviais, ler:

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`, se existir
3. `COMMANDS.md`, se existir
4. `docs/ai/DAILY_AGENT_WORKFLOW.md`
5. `tasks/todo.md`
6. `tasks/lessons.md`

## Carregamento Condicional

| Situação | Documentos a abrir |
|---|---|
| Refactor | `docs/ai/policies/SAFE_REFACTOR_POLICY.md`, `docs/ai/workflows/20-safe-refactor.md` |
| Feature | `docs/ai/workflows/10-feature-delivery.md` |
| Bugfix | `docs/ai/workflows/30-bugfix.md` |
| Revisão | `docs/ai/workflows/40-quality-review.md`, `docs/ai/ops/QUALITY_GATES.md` |
| Arquitetura | `docs/architecture/`, `docs/adr/` |
| Base de dados | `docs/architecture/database.md`, skill de DB se existir |
| Segurança | `SECURITY.md`, `docs/ai/policies/SECRETS_POLICY.md` |
| Dependências | `docs/ai/policies/DEPENDENCY_POLICY.md` |
| README/docs | `docs/ai/policies/LANGUAGE_POLICY.md`, `docs/ai/skills/professional-documentation/SKILL.md` |
| Release | `docs/ai/workflows/50-release-handoff.md`, `CHANGELOG.md`, `VERSION` |

## Proibido

- Carregar todos os ficheiros de `docs/ai/` sem necessidade.
- Carregar instruções de ferramentas sem relação direta com a tarefa.
- Dar prioridade a instruções duplicadas de adaptadores sobre `AGENTS.md`.
- Ignorar código real porque a documentação diz algo diferente.

## Resolução de Conflitos

Quando houver conflito:

1. Instrução explícita do utilizador.
2. Segurança e preservação de dados.
3. Código real e comandos reais.
4. `PROJECT_CONTEXT.md`.
5. `AGENTS.md`.
6. Documento específico relevante.
7. Adaptador da ferramenta.

## Sinal de Excesso de Contexto

Se o agente começar a propor alterações fora do pedido, assumir excesso de contexto e reduzir para:

- objetivo do utilizador;
- ficheiros afetados;
- comandos reais;
- política específica da tarefa.
