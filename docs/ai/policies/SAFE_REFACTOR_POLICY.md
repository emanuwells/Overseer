# Política de Refactor Seguro

## Regra principal

Refactor estrutural exige plano antes de código, execução por fases e validação objetiva.

## Antes de alterar código

Obrigatório:

1. Identificar comportamento atual.
2. Mapear ficheiros e dependências afetadas.
3. Identificar APIs públicas, contratos, endpoints e formatos de dados.
4. Separar refactor de novas funcionalidades.
5. Propor fases pequenas.
6. Definir validação por fase.
7. Definir rollback.
8. Listar riscos.

## Durante o refactor

- Uma área funcional de cada vez.
- Uma camada de cada vez quando possível.
- Preservar comportamento.
- Atualizar imports e referências.
- Evitar renomeações cosméticas sem ganho.
- Evitar abstrações prematuras.
- Parar se testes falharem sem causa clara.

## Depois de cada fase

Registar:

- ficheiros alterados;
- motivo;
- validação executada;
- riscos residuais;
- próximos passos;
- rollback.

## Proibido

- Reescrever o projeto inteiro de uma vez.
- Alterar comportamento sem declarar.
- Mudar schema de produção sem plano de migração.
- Apagar código aparentemente morto sem verificar referências.
- Introduzir dependências para evitar análise do código existente.

## Critério de conclusão

```text
[ ] Comportamento preservado ou alteração declarada.
[ ] Fases concluídas individualmente.
[ ] Testes/build/lint/typecheck executados ou limitação justificada.
[ ] README/COMMANDS/CHANGELOG/tasks atualizados quando aplicável.
[ ] Auditoria de limpeza executada.
[ ] Rollback possível ou limitação declarada.
```
