# Quality Gates

## Objetivo

Definir critérios de qualidade proporcionais ao risco de cada alteração.

## Gates por Risco

### Baixo (texto, README, ajuste local)

- [ ] Revisão visual do diff
- [ ] Verificar que não há segredos expostos

### Médio (script, componente, endpoint)

- [ ] Revisão do diff
- [ ] Testes unitários passam ou limitação justificada
- [ ] Lint passa ou justificativa documentada
- [ ] Verificar imports e referências

### Alto (backend, API, DB, Docker)

- [ ] Todos os gates anteriores
- [ ] Testes de integração passam
- [ ] Build compila sem erros
- [ ] Validação manual do comportamento
- [ ] Rollback documentado

### Crítico (produção, SSH, migrações)

- [ ] Todos os gates anteriores
- [ ] Revisão por par
- [ ] Backup verificado
- [ ] Plano de rollback testado
- [ ] Monitorização preparada

## Comandos de Validação

Verificar `COMMANDS.md` para comandos reais de validação.

## Critérios de Pass/Fail

- Todos os gates aplicáveis devem passar
- Falhas devem ser documentadas com justificação
- Limitações devem ser registadas em `tasks/lessons.md`