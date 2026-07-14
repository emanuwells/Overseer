# Repository Hygiene Policy

## Objetivo

Manter o repositório limpo, organizado e fácil de navegar.

## Regras de Limpeza

### Ficheiros Temporários

Remover ou ignorar:

- `__pycache__/`
- `*.pyc`
- `*.pyo`
- `.pytest_cache/`
- `.mypy_cache/`
- `*.egg-info/`
- `node_modules/`
- `.DS_Store`
- `Thumbs.db`

### Ficheiros Gerados

Não versionar:

- Builds e artefactos
- Logs
- Backups
- Cache de IDE

### Imports Não Utilizados

Remover imports não utilizados:

```python
# Antes
import os
import sys
from typing import List  # Não usado

# Depois
import os
```

### Código Morto

- Identificar antes de remover
- Verificar referências
- Documentar remoção

## Verificações Regulares

### Antes de Commit

- [ ] `git status` mostra apenas ficheiros relevantes
- [ ] Sem imports não utilizados
- [ ] Sem secrets ou dados sensíveis
- [ ] Sem código comentado desnecessário

### Auditoria Periódica

- Verificar `.gitignore` está atualizado
- Limpar branches merged
- Remover tags obsoletas
- Verificar dependências desnecessárias

## Estrutura da Raiz

Seguir `AGENTS.md` — Raiz Limpa:

**Permitido na raiz:**
- `README.md`, `AGENTS.md`, `COMMANDS.md`, `CHANGELOG.md`
- `PROJECT_CONTEXT.md` (se preenchido)
- `VERSION`, `LICENSE`
- `.gitattributes`, `.gitignore`
- `.github/`, `deploy/`, `docker/`, `docs/`, `frontend/`, `openapi/`, `runtime/`, `scripts/`, `secrets/`, `src/`, `tasks/`, `tests/`, `tools/`

**Fora da raiz:**
- templates de configuração → `docs/resources/templates/`
- `CONTRIBUTING.md` → `docs/governance/`
- `SECURITY.md` → `.github/`

## Deteção de Problemas

```bash
# Ficheiros não rastreados
git status --porcelain

# Imports não utilizados
pip install autoflake
autoflake --remove-unused-imports -r src/

# Código morto
vulture src/ --min-confidence 80
