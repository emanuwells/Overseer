# Definition of Done

## Critérios Universais

Para qualquer entrega de código, documentação, configuração ou alteração estrutural:

### Funcionalidade

- [ ] Comportamento implementado conforme especificado
- [ ] Casos de borda tratados
- [ ] Edge cases documentados ou justificação para não tratamento

### Código

- [ ] Código legível e modular
- [ ] Type hints presentes onde aplicável
- [ ] Docstrings para funções públicas
- [ ] Sem dependências desnecessárias
- [ ] Imports organizados

### Testes

- [ ] Testes unitários para lógica de domínio
- [ ] Testes de integração para API e DB
- [ ] Testes cobrem caminho feliz e erros comuns
- [ ] Testes passam consistentemente

### Documentação

- [ ] README atualizado se mudou uso ou instalação
- [ ] COMMANDS.md atualizado se mudou comandos
- [ ] CHANGELOG.md atualizado se alteração versionável
- [ ] Documentação de arquitetura se mudou estrutura

### Segurança

- [ ] Sem segredos hardcoded
- [ ] Validação de input
- [ ] Erros não expõem informação sensível

### Operacional

- [ ] Docker build passa (se aplicável)
- [ ] Configuração de ambiente documentada
- [ ] Rollback possível

## Entrega

- Diff revisto
- Ficheiros alterados listados
- Validações executadas e resultado
- Limitações conhecidas
- Próximos passos, se aplicável