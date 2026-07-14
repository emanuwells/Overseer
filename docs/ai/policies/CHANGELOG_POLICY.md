# Changelog Policy

## Objetivo

Manter um registo claro e útil de alterações versionáveis.

## Formato

Usar [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [MAJOR.MINOR.PATCH] - YYYY-MM-DD

### Added
- New feature

### Changed
- Change in existing functionality

### Deprecated
- Feature that will be removed in future

### Removed
- Feature removed

### Fixed
- Bug fix

### Security
- Security improvement
```

## O Que Registar

### Sempre

- Novas funcionalidades
- Alterações de API
- Breaking changes
- Deprecações
- Correções de bugs importantes
- Alterações de configuração
- Alterações de segurança

### Opcional

- Melhorias de performance
- Alterações de documentação
- Refactors com benefício visível

### Nunca

- Correções ortográficas
- Ajustes cosméticos
- Alterações em código não funcional

## Regras

1. Uma entrada por alteração
2. Agrupar por tipo (Added, Changed, etc.)
3. Ordenar do mais recente para o mais antigo
4. Data no formato ISO (YYYY-MM-DD)
5. Links para issues/PRs quando aplicável

## Processo

1. Adicionar entrada durante desenvolvimento
2. Atualizar versão em `VERSION`
3. Fechar secção Unreleased
4. Criar git tag no release

## Seção Unreleased

Manter secção para alterações não lançadas:

```markdown
## [Unreleased]

### Added
- Feature in progress
```

## Breaking Changes

Indicar claramente:

```markdown
### Changed
- **BREAKING** Old behavior removed, use new approach