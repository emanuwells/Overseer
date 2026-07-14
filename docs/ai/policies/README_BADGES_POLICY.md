# README Badges Policy

## Princípios

Badges devem comunicar informação útil e atualizada. Badges desatualizados ou irrelevantes devem ser removidos.

## Badges Recomendados

### CI/CD

- Build status (GitHub Actions, Travis, etc.)
- Coverage (se > 80%)
- Lint/Quality (se configurado)

### Metadata

- License
- Version (se relevante)

### Social (opcional)

- GitHub stars (se público e relevante)

## Badges Não Recomendados

- Badges de serviços não utilizados
- Badges com informação redundante
- Badges que requerem configuração externa complexa
- Badges de "powered by" não essenciais

## Formato

Usar shields.io ou serviço oficial:

```markdown
[![Build Status](https://github.com/user/repo/actions/workflows/ci.yml/badge.svg)](link)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

## Positioning

1. Título e descrição breve
2. Badges
3. Badges de instalação/setup
4. Índice (se longo)

## Exemplo

```markdown
# Project Name

Brief description of what this project does.

[![CI](https://github.com/user/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/user/repo/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)

## Quick Start

...
```

## Manutenção

- Verificar badges mensalmente
- Remover badges de serviços desativados
- Atualizar links quebrados