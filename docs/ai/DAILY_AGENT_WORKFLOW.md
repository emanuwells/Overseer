# Workflow Diário da Equipa IA

## Objetivo

Dar ao programador solo um fluxo repetível para usar IA como equipa sénior sem perder controlo técnico.

## Fluxo Universal

### 1. Entrada

- Reescrever o pedido em objetivo técnico claro.
- Identificar se é feature, bugfix, refactor, documentação, DevOps, dados ou revisão.
- Classificar risco: baixo, médio, alto ou crítico.

### 2. Contexto

Ler apenas o necessário:

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`, se existir
3. `COMMANDS.md`, se existir
4. `tasks/todo.md`
5. `tasks/lessons.md`
6. documentos específicos indicados pela `CONTEXT_BUDGET_POLICY.md`

### 3. Plano

Para risco médio ou superior, produzir plano curto com:

- objetivo;
- ficheiros afetados;
- validações;
- rollback;
- critérios de conclusão.

### 4. Execução

- Trabalhar em incrementos pequenos.
- Alterar uma responsabilidade de cada vez.
- Manter comportamento existente salvo pedido contrário.
- Evitar dependências novas.
- Não misturar limpeza ampla com feature.

### 5. Validação

Executar, quando existirem:

- lint;
- typecheck;
- testes;
- build;
- validação manual mínima;
- revisão do diff.

Se não existir comando, registar que não existe validação automática definida em `COMMANDS.md`.

### 6. Registo

Atualizar:

- `tasks/todo.md`: o que foi feito, pendente e validado;
- `tasks/lessons.md`: só aprendizagens reutilizáveis;
- `CHANGELOG.md`: alterações versionáveis;
- `README.md`/`docs/architecture/`: se mudou uso ou arquitetura.

### 7. Handoff

No fim, entregar:

- resumo;
- ficheiros alterados;
- validações executadas;
- riscos ou limitações;
- próximo passo objetivo, se existir.

## Regra de Ouro

A IA pode executar como equipa sénior, mas o programador continua a decidir sobre alterações irreversíveis, produção, segredos, dependências relevantes e mudanças arquiteturais grandes.
