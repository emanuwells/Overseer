---
name: ssh-server-ops
description: Usar SSH, GitHub e servidores com segurança.
---

# SSH Server Ops

## Quando Usar

Usar para GitHub via SSH, produção, deploy, logs e operações remotas.

## Objetivo

Usar SSH, GitHub e servidores com segurança.

## Procedimento

1. Ler `AGENTS.md` e aplicar regras de proporcionalidade.
2. Confirmar contexto real antes de alterar ficheiros.
3. Não inventar informação.
4. Preservar alterações existentes do utilizador.
5. Aplicar a solução mínima que resolve o problema.
6. Atualizar documentação, handoff e changelog quando aplicável.
7. Validar o resultado antes de concluir.

## Regras Específicas

- Nunca expor chaves privadas ou segredos.
- Confirmar servidor, pasta, branch e impacto antes de produção.
- Não executar comandos destrutivos sem autorização.
- Preferir GitHub via SSH se já estiver configurado.

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
