# Version and License Policy

## Versionamento

### Ficheiro VERSION

- Localização: `VERSION` na raiz
- Formato: `MAJOR.MINOR.PATCH` (ex: `1.0.0`)
- Atualização: conforme `CHANGELOG_POLICY.md`

### Semântica de Versão

| Componente | Quando Incrementar |
|---|---|
| MAJOR | Breaking changes na API ou comportamento |
| MINOR | Novas funcionalidades compatíveis |
| PATCH | Correções de bugs compatíveis |

### Git Tags

- Formato: `vMAJOR.MINOR.PATCH` (ex: `v1.0.0`)
- Anotadas com mensagem descritiva
- Criadas no momento do release

## Licença

### Ficheiro LICENSE

- Localização: `LICENSE` na raiz
- Tipo: MIT License
- Deve estar presente e atualizado

### Cabeçalho de Ficheiros

Para ficheiros de código novos:

```python
# Copyright (c) 2024 Emanuel Wells
# SPDX-License-Identifier: MIT
```

## Alterações Versionáveis

Registar em `CHANGELOG.md`:

- Novas funcionalidades
- Alterações de API
- Deprecações
- Correções de bugs
- Alterações de configuração
- Alterações de documentação

## Não Versionáveis

Não registar em `CHANGELOG.md`:

- Ajustes cosméticos
- Refactors sem alteração de comportamento
- Correções ortográficas
- Alterações em documentação não funcional