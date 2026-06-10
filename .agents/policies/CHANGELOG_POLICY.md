# CHANGELOG_POLICY.md

Política obrigatória para manter `CHANGELOG.md` atualizado de forma versionada e rastreável.

## Regra Principal

Qualquer IA que altere código, documentação, configuração, estrutura, scripts, dependências, dados de exemplo, MCP, Skills, ADRs ou decisões técnicas deve atualizar `CHANGELOG.md` na mesma tarefa, antes de entregar o trabalho.

## Objetivo

Garantir que o histórico permite responder:

1. O que mudou?
2. Porque mudou?
3. Que impacto teve?
4. Que MCP/Skills foram usados?
5. Como foi verificado?
6. Que dependências ou ficheiros foram adicionados/removidos?
7. Houve impacto em SSH, deploy ou produção?

## Obrigatoriedade

`CHANGELOG.md` é obrigatório quando houver:

- código novo;
- correção de bug;
- refactor;
- alteração de arquitetura;
- alteração de base de dados;
- migration nova;
- alteração de endpoint, contrato de API ou payload;
- alteração de Docker, CI/CD, variáveis de ambiente ou configuração;
- alteração de dependências, manifestos ou lockfiles;
- criação/alteração de `requirements.txt`, `pyproject.toml`, `package.json`, `composer.json` ou equivalente;
- alteração de documentação;
- alteração de badges, arquitetura, estrutura do projeto ou Docker no `README.md`;
- alteração de regras em `AGENTS.md`;
- alteração de `PROJECT_CONTEXT.md`;
- alteração de `.agents/ops/HANDOFF.md` quando representar mudança operacional relevante;
- alteração de Skills em `.agents/skills/` ou `.claude/skills/`;
- alteração de MCP servers ou configuração MCP;
- alteração de política SSH, deploy ou servidores;
- criação/atualização de ADRs;
- alteração de scripts, jobs, agentes ou automações;
- remoção, renomeação ou movimentação de ficheiros;
- decisão técnica que afete trabalho futuro.

Se a tarefa for apenas análise, diagnóstico ou explicação sem alteração de ficheiros, `CHANGELOG.md` não precisa de nova entrada.

## SemVer

Usar SemVer: `MAJOR.MINOR.PATCH`.

- `PATCH`: correções, ajustes pequenos, documentação sem nova capacidade.
- `MINOR`: nova capacidade compatível, novo ficheiro operacional, nova Skill, novo MCP opcional, nova política compatível.
- `MAJOR`: quebra de compatibilidade, mudança estrutural que exige migração manual ou alteração incompatível de contrato público.

Usar o menor incremento que represente corretamente o impacto.

## Data E Hora

Cada entrada deve usar ISO 8601 com timezone Europe/Lisbon.

Exemplo:

```text
2026-06-03T13:45:00+01:00
```

## Formato Obrigatório

```markdown
## [VERSAO] - YYYY-MM-DDTHH:mm:ss+TZ

### Título Curto Da Alteração

**Motivo:**
Explicar porque a alteração foi feita.

**Impacto:**
Explicar o que muda no projeto, utilizador, arquitetura ou operação.

**Alterações:**
- `ficheiro/ou/pasta`: descrição objetiva da alteração.

**Dependências:**
- Manifestos alterados ou `N/A — motivo`.

**Ferramentas, MCP E Skills:**
- MCP servers usados ou `N/A — motivo`.
- Skills usadas ou `N/A — motivo`.
- Fallbacks aplicados, se existirem.

**SSH / Servidores:**
- Servidores acedidos/comandos remotos ou `N/A — motivo`.

**Ficheiros Removidos Ou Obsoletos:**
- Removidos, candidatos ou `N/A — motivo`.

**Testes:**
- Comando executado e resultado.
- Se não aplicável: `N/A — motivo`.

**Validação:**
- Como foi confirmado que a alteração está correta.

**Refs:**
- Links, issues, commits, pedidos do utilizador ou `N/A`.

**Diff:**
Resumo curto do diff lógico.

---
```

## MCP

Atualizar `CHANGELOG.md` quando houver:

- criação/alteração de configs MCP;
- criação/alteração de `.agents/mcp/`;
- adição/remoção de MCP server recomendado;
- alteração de permissões, escopos ou política MCP.

## Checklist Final Obrigatória

```text
[ ] Verifiquei se a tarefa altera ficheiros, comportamento, configuração, documentação ou decisão técnica.
[ ] Atualizei CHANGELOG.md quando aplicável.
[ ] Atualizei .agents/ops/HANDOFF.md quando houve tarefa não trivial ou alteração operacional.
[ ] Registei MCP servers e Skills usados ou justifiquei N/A.
[ ] Registei dependências/manifestos alterados ou justifiquei N/A.
[ ] Registei SSH/servidores quando aplicável.
[ ] Registei ficheiros removidos ou candidatos a remoção.
[ ] Criei/atualizei ADRs quando houve decisão técnica relevante.
[ ] Usei SemVer corretamente.
[ ] Usei data/hora ISO 8601 Europe/Lisbon.
[ ] Listei ficheiros alterados.
[ ] Registei testes ou justifiquei N/A.
[ ] Registei validação.
```

## Proibição De Entrega Sem Changelog

Se houve alteração versionável, a IA não deve entregar como concluído enquanto não atualizar `CHANGELOG.md`.
