# MCP Servers — Databases

MCPs de base de dados são úteis, mas críticos.

## Quando Usar

- inspeção de schema;
- queries read-only;
- validação de dados;
- diagnóstico;
- apoio a migrations.

## Regras

- preferir utilizadores read-only;
- nunca guardar connection strings reais no Git;
- confirmar base de dados e ambiente;
- não executar `DROP`, `TRUNCATE`, `DELETE`, `UPDATE` ou migrations sem confirmação explícita;
- fazer backup antes de operações destrutivas;
- registar comandos e impacto em handoff/changelog.

## MCPs Possíveis

- SQLite;
- PostgreSQL;
- MySQL/MariaDB.

## Configuração Segura

Usar placeholders nos exemplos:

```json
{
  "DB_HOST": "localhost",
  "DB_PORT": "3306",
  "DB_DATABASE": "example_database",
  "DB_USERNAME": "example_user",
  "DB_PASSWORD": "example_password"
}
```

Valores reais devem ir para `.env`, `.secrets/` ou secret manager.
