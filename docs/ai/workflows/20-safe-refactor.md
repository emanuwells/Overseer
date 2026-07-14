# Workflow 20 — Refactor Seguro

## Objetivo

Melhorar estrutura sem alterar comportamento funcional.

## Passos

1. Não alterar código inicialmente.
2. Mapear comportamento atual e dependências.
3. Dividir em fases pequenas.
4. Definir rollback por fase.
5. Executar uma fase de cada vez.
6. Atualizar imports, testes e documentação afetada.
7. Validar após cada fase.
8. Parar se surgir falha sem causa entendida.

## Critérios

- comportamento preservado;
- diff compreensível;
- validação executada ou limitação documentada;
- sem ficheiros temporários inúteis;
- changelog atualizado.
