# Decisions

## Visão Geral

Registo de decisões técnicas permanentes ou compromissos relevantes.

## Formato ADR (Architecture Decision Record)

```markdown
## ADR-XXX: [Título]

**Data**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded
**Contexto**: [Problema ou situação]
**Decisão**: [Solução chosen]
**Alternativas**: [Opções consideradas]
**Consequências**: [Impacto da decisão]

### Prós
- [pró 1]
- [pró 2]

### Contras
- [contra 1]
- [contra 2]
```

## Decisões Registadas

### ADR-001: Docker-first Architecture

**Data**: 2024-01-01
**Status**: Accepted
**Contexto**: Necessidade de deployment consistente entre ambientes
**Decisão**: Todo o stack corre em Docker, com Docker Compose para desenvolvimento
**Alternativas**: 
- Deployment direto em VMs
- Kubernetes para orquestração
**Consequências**: 
- Curva de aprendizagem Docker
- Portabilidade garantida
- Overhead de containerização

### ADR-002: FastAPI para API REST

**Data**: 2024-01-01
**Status**: Accepted
**Contexto**: Necessidade de API performática com validação automática
**Decisão**: FastAPI com Pydantic para validação e OpenAPI automático
**Alternativas**:
- Flask (menos validação automática)
- Django (overkill para este projeto)
**Consequências**:
- Type hints obrigatórios
- Documentação OpenAPI automática
- Performance alta

### ADR-003: PostgreSQL como base de dados

**Data**: 2024-01-01
**Status**: Accepted
**Contexto**: Necessidade de persistência relacional com JSON
**Decisão**: PostgreSQL com SQLAlchemy ORM
**Alternativas**:
- SQLite (limitado para produção)
- MongoDB (schema menos rígido, mas menos adequado)
**Consequências**:
- Migrations via Alembic
- JSONB para dados semi-estruturados
- Suporte a full-text search

### ADR-004: Vanilla JS para Frontend

**Data**: 2024-01-01
**Status**: Accepted
**Contexto**: Dashboard simples sem necessidade de framework SPA
**Decisão**: HTML/CSS/JS vanilla com fetch API
**Alternativas**:
- React/Vue (overkill para dashboard simples)
- Server-side rendering (menos interativo)
**Consequências**:
- Zero build step
- Manutenção simples
- Funcionalidade limitada a dashboards

## Adicionar Decisão

Para adicionar uma nova decisão:

1. Criar secção com formato ADR
2. Numerar sequencialmente
3. Incluir data, contexto, decisão e consequências
4. Documentar alternativas consideradas