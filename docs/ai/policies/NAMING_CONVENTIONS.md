# Naming Conventions

## Princípios

- Nomes claros e descritivos
- Auto-documentados quando possível
- Consistentes com a stack
- Evitar abreviações obscuras

## Python

### Ficheiros

- Módulos: `snake_case.py`
- Pacotes: `snake_case/`
- Testes: `test_<module>_<feature>.py`

### Funções e Variáveis

- `snake_case`
- Verbos para funções: `get_`, `create_`, `update_`, `delete_`
- Substantivos para variáveis: `pipeline`, `run_data`

### Classes

- `PascalCase`
- Nomes descritivos: `PipelineMonitor`, `RunScheduler`

### Constantes

- `UPPER_SNAKE_CASE`
- Nomes descritivos: `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT`

## Frontend (HTML/CSS/JS)

### Ficheiros

- HTML: `kebab-case.html`
- CSS: `kebab-case.css`
- JS: `kebab-case.js`

### Classes CSS

- `kebab-case`
- Prefixo semântico: `.ov-`, `.overseer-`

### IDs HTML

- `kebab-case`
- Únicos na página

### Variáveis JS

- `camelCase` para variáveis locais
- `PascalCase` para classes/construtores
- `UPPER_SNAKE_CASE` para constantes

## Base de Dados

### Tabelas

- `snake_case`
- Plural: `pipelines`, `runs`, `deployments`

### Colunas

- `snake_case`
- Prefixo quando útil: `pipeline_id`, `run_status`

### Índices

- `idx_<table>_<columns>`
- `uq_<table>_<columns>` para unique

## API REST

### Endpoints

- `kebab-case` ou `snake_case`
- Plural para coleções: `/api/pipelines`
- Verbos para ações: `/api/pipelines/sync`

### Headers

- `X-Overseer-*` para headers customizados

## Git

### Branches

- `feature/<descrição>`
- `bugfix/<descrição>`
- `hotfix/<descrição>`
- `refactor/<descrição>`

### Commits

- Formato: `<tipo>(<scope>): <descrição>`
- Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Docker

### Imagens

- `overseer-<componente>`
- Tags: `latest`, `v1.0.0`

### Containers

- `overseer-api`, `overseer-monitor`