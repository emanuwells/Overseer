---
name: file-pruner
description: Auditar e remover ficheiros desnecessários com segurança.
---

# File Pruner

## Quando Usar

Usar em cada tarefa para identificar duplicados, temporários, artefactos e obsoletos.

## Objetivo

Auditar e remover ficheiros desnecessários com segurança.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Auditar ficheiros desnecessários em cada pedido.
- Remover automaticamente apenas quando for claramente seguro.
- Pedir confirmação em caso de dúvida.
- Nunca remover migrations, backups, configs, dados, scripts de produção ou alterações do utilizador sem confirmação.

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
