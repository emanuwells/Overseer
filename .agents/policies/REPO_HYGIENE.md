# REPO_HYGIENE.md

Auditoria leve do repositório em cada iteração.

## Objetivo

Evitar acumulação de scripts, ficheiros, documentação, configs e dependências que já não fazem sentido.

## Regra Principal

Em cada pedido, a IA deve verificar se há elementos claramente desnecessários, duplicados, obsoletos ou fora das regras.

A IA deve remover automaticamente apenas o que for claramente seguro.

Se houver dúvida, deve listar candidatos e pedir confirmação.

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
- ficheiros que contradizem as policies.

## Pode Remover Sem Confirmação

Apenas quando for inequívoco:

- temporários criados pela IA na tarefa atual;
- duplicados óbvios;
- artefactos de build acidentais;
- ficheiros vazios sem referências;
- documentação substituída e sem ligações.

## Nunca Remover Sem Confirmação

- migrations;
- backups;
- dados;
- configs;
- `.env` reais;
- scripts de produção;
- documentação legal/auditoria;
- ficheiros alterados pelo utilizador;
- código aparentemente morto mas não confirmado.

## Registo

Quando houver limpeza, registar:

- `CHANGELOG.md`, se for alteração versionável;
- `.agents/ops/HANDOFF.md`, em tarefas não triviais;
- resposta final com resumo.
