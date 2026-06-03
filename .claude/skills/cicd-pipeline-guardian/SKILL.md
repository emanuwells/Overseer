---
name: cicd-pipeline-guardian
description: Proteger pipelines.
---

# CI/CD Pipeline Guardian

## Quando Usar

Usar em GitHub Actions, deploy, testes automáticos e secrets.

## Objetivo

Proteger pipelines.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Usar secrets do CI/CD, nunca valores reais no repo.
- Instalar dependências a partir de manifestos versionados.
- Evitar deploy automático perigoso sem gates.
- Documentar comandos e ambientes.

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
