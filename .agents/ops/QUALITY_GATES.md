# QUALITY_GATES.md

Quality gates por tipo de alteração.

## Regra Principal

Executar os gates proporcionais ao risco da tarefa. Se não for possível, justificar.

## Gate Universal

```text
[ ] Sem segredos.
[ ] Naming profissional.
[ ] Higiene do repositório revista.
[ ] Documentação atualizada quando aplicável.
[ ] COMMANDS.md atualizado quando comandos mudaram.
[ ] CHANGELOG.md atualizado quando houve alteração versionável.
```

## Frontend

```text
[ ] Lint passa.
[ ] Typecheck passa.
[ ] Build passa.
[ ] Estados loading/error/empty revistos.
[ ] Acessibilidade básica revista.
[ ] Responsividade revista.
[ ] Testes executados quando existem.
```

## Backend

```text
[ ] Testes passam.
[ ] Validação de input revista.
[ ] Erros e logs revistos.
[ ] Contrato API validado.
[ ] Sem segredos em logs/respostas.
[ ] Migrations revistas quando aplicável.
```

## Full-Stack

```text
[ ] Frontend build passa.
[ ] Backend/testes passam.
[ ] Contrato API coerente.
[ ] Env vars documentadas.
[ ] Fluxo ponta-a-ponta validado quando possível.
```

## Docker/Deploy

```text
[ ] Compose/Dockerfile validado.
[ ] Portas e volumes documentados.
[ ] Healthcheck/logs revistos.
[ ] Rollback conhecido.
[ ] Sem segredos em imagens/configs.
```

## Produção

```text
[ ] Servidor confirmado.
[ ] Pasta confirmada.
[ ] Branch confirmada.
[ ] Backup/rollback considerado.
[ ] Comando exato confirmado.
[ ] Impacto explicado.
```
