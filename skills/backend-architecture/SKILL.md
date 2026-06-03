---
name: backend-architecture
description: Backend profissional.
---

# Backend Architecture

## Quando Usar

Usar em APIs, autenticação, validação, serviços, logs e erros.

## Objetivo

Backend profissional.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Validar inputs, erros, logs e contratos.
- Separar controllers, serviços, persistência e configuração quando fizer sentido.
- Não expor segredos ou stack traces em produção.
- Documentar endpoints relevantes.

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
