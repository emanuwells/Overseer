---
name: refactor-minimal
description: Refactor pequeno e seguro.
---

# Refactor Minimal

## Quando Usar

Usar para reduzir duplicação ou complexidade sem reescrever tudo.

## Objetivo

Refactor pequeno e seguro.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Aplicar regras gerais do `AGENTS.md`.
- Usar apenas informação confirmada.
- Manter solução simples, segura e verificável.

## Checklist

```text
[ ] Contexto validado.
[ ] Riscos identificados.
[ ] Alteração mínima aplicada.
[ ] Documentação atualizada quando aplicável.
[ ] Testes/validação executados ou justificados.
[ ] Changelog atualizado quando aplicável.
[ ] Handoff atualizado quando aplicável.
```
