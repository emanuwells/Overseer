# Evidence

## Objetivo

Documentar evidências de validação executada para rastreabilidade e auditoria.

## Quando Usar

Registar evidências quando:

- Comandos de validação foram executados
- Testes foram corridos
- Build foi verificado
- Erros foram encontrados e tratados
- Limitações foram identificadas

## Formato

```text
## Evidência: [Descrição]

**Data**: YYYY-MM-DD HH:MM
**Executado por**: [humano/IA]
**Comando**: [comando real executado]
**Resultado**: [pass/fail/error]
**Output relevante**: [trecho do output]

### Notas
- [observações]
```

## Exemplos

### Testes Executados

```text
## Evidência: Testes unitários

**Data**: 2026-06-23 10:00
**Comando**: pytest tests/ -v
**Resultado**: Pass (23/23)

```
tests/test_api_contract.py::test_get_pipeline PASSED
tests/test_api_contract.py::test_create_pipeline PASSED
...
```

### Build Verificado

```text
## Evidência: Docker build

**Data**: 2026-06-23 10:15
**Comando**: docker build -t overseer:latest .
**Resultado**: Success

### Notas
- Imagem criada com sucesso
- Health check passa
```

### Erro Encontrado

```text
## Evidência: Teste falhou

**Data**: 2026-06-23 10:30
**Comando**: pytest tests/test_retention_purge.py
**Resultado**: Fail

```
FAILED tests/test_retention_purge.py::test_purge_old_runs
AssertionError: Expected 5 deleted, got 3
```

### Ação Tomada
- Corrigido query de purge em `src/overseer_core/retention.py`
- Teste passa após correção
```

## Localização

- Em `tasks/todo.md` para tarefas em curso
- Em `docs/ai/ops/HANDOFF.md` para entregas
- Em `docs/ai/ops/DECISIONS.md` para decisões técnicas