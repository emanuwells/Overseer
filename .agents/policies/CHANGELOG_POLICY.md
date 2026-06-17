# CHANGELOG_POLICY.md

Política de changelog.

## Regra principal

Qualquer alteração versionável deve ser registada em `CHANGELOG.md`.

## Alterações Versãoáveis

- código;
- documentação;
- configuração;
- dependências;
- Docker;
- CI/CD;
- scripts;
- estrutura;
- policies;
- competências;
- `secrets/examples`;
- modelos;
- remoção/renomeação de ficheiros;
- decisões técnicas.

## SemVer

- PATCH: correções e ajustes pequenos.
- MINOR: nova funcionalidade compatível.
- MAJOR: alteração estrutural/incompatível.

## Formato

```markdown
## [VERSAO] - YYYY-MM-DDTHH:mm:ss+TZ

### Título

**Motivo:**
Texto.

**Impacto:**
Texto.

**Alterações:**
- `ficheiro`: descrição.

**Validação:**
- comando ou justificação.

**Diff:**
Resumo.
---
```


## MCP

Atualizar `CHANGELOG.md` quando houver:

- criação/alteração de configs MCP;
- criação/alteração de `.agents/mcp/`;
- adição/remoção de MCP server recomendado;
- alteração de permissões, escopos ou política MCP.
