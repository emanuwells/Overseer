# Agent Compliance

## Objetivo

Garantir que agentes IA cumprem o contrato operacional do projeto.

## Checklist de Compliance

Antes de entregar trabalho, verificar:

### Documentação

- [ ] `AGENTS.md` lido e compreendido
- [ ] `PROJECT_CONTEXT.md` consultado (se existir)
- [ ] `COMMANDS.md` consultado (se existir)
- [ ] `tasks/todo.md` atualizado (se não trivial)
- [ ] `tasks/lessons.md` atualizado (se aplicável)

### Qualidade

- [ ] Código preserva comportamento existente (salvo declaração)
- [ ] Sem misturar feature, bugfix, refactor
- [ ] Sem introduzir dependências sem justificação
- [ ] Sem versionar segredos reais
- [ ] Sem declarar validações não executadas

### Segurança

- [ ] Segredos não expostos em logs
- [ ] Credenciais não em código
- [ ] Validação de input
- [ ] Erros não expõem stack traces

### Operacional

- [ ] Diff revisto
- [ ] Ficheiros alterados listados
- [ ] Validações executadas
- [ ] Limitações documentadas
- [ ] Próximos passos claros

## Violações Comuns

| Violação | Correção |
|---|---|
| "Isto liga à DB" | Explicar arquitetura de persistência |
| Alterar sem plano | Criar plano antes de código |
| Dependência sem justificação | Documentar necessidade e risco |
| Teste não executado | Executar ou declarar limitação |
| Segredo em código | Mover para env vars |

## Reportar Violação

Se uma violação for detetada:

1. Documentar a violação
2. Explicar o impacto
3. Propor correção
4. Registar em `tasks/lessons.md`