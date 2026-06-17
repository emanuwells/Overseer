# REPO_HYGIENE.md

Auditoria de higiene do repositório em cada iteração.

## Objetivo

Evitar acumulação de scripts, ficheiros, documentação, configs, pastas e dependências que já não fazem sentido.

## Regra principal

Em cada pedido, a IA deve verificar se há elementos claramente desnecessários, duplicados, obsoletos ou fora das regras.

Em tarefas não triviais, aplicar também `.agents/policies/CLEANUP_AUDIT_POLICY.md`.

Se, após auditoria minuciosa, um elemento for comprovadamente inútil e seguro de remover, a IA deve apagá-lo. Não deve deixá-lo apenas como sugestão.

Se houver dúvida, deve listar o item como candidato e pedir confirmação antes de apagar.

## Verificar Sempre

- scripts temporários;
- ficheiros duplicados;
- documentação obsoleta;
- artefactos de build versionados;
- ficheiros gerados pela IA na tarefa atual;
- dependências não usadas;
- configurações antigas;
- pastas vazias;
- nomes fora da convenção;
- ficheiros que contradizem as policies;
- pastas que não pertencem à arquitetura real do projeto;
- saídas intermédios substituídos por artefactos finais.

## Pode Remover Sem Confirmação

Apenas quando for inequívoco e depois de auditoria:

- temporários criados pela IA na tarefa atual;
- duplicados óbvios sem referências;
- artefactos de build/cache acidentais;
- ficheiros vazios sem referências;
- pastas vazias sem propósito documentado;
- documentação substituída e sem ligações;
- saídas intermédios que já foram incorporados no artefacto final.

## Nunca Remover Sem Confirmação

- migrações;
- backups;
- dados;
- configurações reais;
- `.env` reais;
- certificados, tokens, chaves ou segredos;
- scripts de produção;
- documentação legal/auditoria/compliance;
- ficheiros alterados pelo utilizador;
- código aparentemente morto mas não confirmado;
- assets binários não analisados;
- fluxos de trabalho de CI/CD, Docker, deploy ou infra.

## Registo

Quando houver limpeza, registar:

- `CHANGELOG.md`, se for alteração versionável;
- `tasks/todo.md`, em iterações não triviais;
- `tasks/lessons.md`, se houver aprendizagem reutilizável;
- `.agents/ops/HANDOFF.md`, em tarefas não triviais;
- `.agents/ops/EVIDENCE.md` ou resposta final com resumo da auditoria.
