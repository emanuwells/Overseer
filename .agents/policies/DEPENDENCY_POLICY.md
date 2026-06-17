# DEPENDENCY_POLICY.md

Política de dependências e manifestos.

## Regra principal

Se o projeto, script, pipeline, job, notebook ou automação precisar de dependências externas, deve existir manifesto adequado ao ecossistema.

Não instalar dependências manualmente sem deixar o projeto reprodutível.

## Manifestos

| Ecossistema | Manifesto |
|---|---|
| Python simples | `requirements.txt` |
| Python moderno | `pyproject.toml` |
| Python com Poetry/uv | `poetry.lock`, `uv.lock` |
| Node.js | `package.json` + lockfile |
| PHP | `composer.json` + `composer.lock` |
| .NET | `.csproj`, `.sln` |
| Java/Kotlin | `pom.xml`, `build.gradle` |
| Docker | `Dockerfile`, `compose.yml` |
| CI/CD | manifestos versionados |

## `requirements.txt`

Criar ou atualizar quando houver:

- script Python com libs externas;
- pipeline Python;
- notebook com pacotes externos;
- automação Python;
- deploy Python simples.

Não incluir standard library.

Exemplo:

```txt
requests>=2.32,<3
python-dotenv>=1.0,<2
```

## Regras

- Evitar dependências desnecessárias.
- Justificar bibliotecas novas quando relevantes.
- Atualizar `COMMANDS.md` com comandos de instalação.
- Atualizar Docker/CI/CD se instalarem dependências.
- Atualizar `CHANGELOG.md` quando aplicável.

## Checklist

```text
[ ] Manifesto correto existe.
[ ] Lockfile atualizado quando aplicável.
[ ] COMMANDS.md atualizado.
[ ] README/PROJECT_CONTEXT atualizados quando aplicável.
[ ] Dependências desnecessárias evitadas.
```
