---
name: dependency-manager
description: Gerir manifestos de dependências.
---

# Dependency Manager

## Quando Usar

Criar/atualizar requirements.txt, package.json, composer.json, lockfiles e instruções.

## Objetivo

Gerir manifestos de dependências.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Garantir manifesto adequado ao ecossistema.
- Python simples usa `requirements.txt` quando não houver `pyproject.toml`/Poetry/uv.
- Não incluir bibliotecas da standard library.
- Atualizar README com comandos de instalação.
- Atualizar Docker/CI/CD quando instalarem dependências.

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
