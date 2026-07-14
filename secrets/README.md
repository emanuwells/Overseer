# Segredos (runtime)

Pasta montada no container Docker (`./secrets:/app/secrets:ro`). Segredos reais ficam aqui e **nunca** entram no Git.

## Exemplos versionados

Copiar a partir de `docs/resources/examples/secrets/`:

```bash
cp docs/resources/examples/secrets/slack.json.example secrets/slack.json
cp docs/resources/examples/secrets/database.json.example.json secrets/database.json
```

Ajustar permissões em Linux: `chmod 600 secrets/*`.

## Variáveis de ambiente

Copiar o template para `secrets/.env` (nunca versionar o ficheiro real):

```bash
cp docs/resources/templates/.env.example secrets/.env
```

Os scripts `dev-ui.ps1`, `overseer-up.sh` e `ensure-env.*` criam ou migram automaticamente a partir da raiz legada.
