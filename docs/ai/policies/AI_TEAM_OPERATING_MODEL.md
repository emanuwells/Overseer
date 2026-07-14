# Modelo Operacional — Solo Dev + Equipa IA Sénior

## Objetivo

Permitir que um programador solo trabalhe com IA como se tivesse uma equipa sénior full stack, sem ficar preso a um IDE ou fornecedor específico.

## Princípios

- O núcleo operacional é neutro: `AGENTS.md`, `docs/ai/` e `docs/ai/`.
- Adaptadores de IDE existem para conveniência, não para controlo.
- A IA deve trabalhar por papéis técnicos relevantes ao risco.
- A IA deve produzir evidência, não apenas confiança verbal.
- Alterações grandes devem ser faseadas, reversíveis e validadas.

## Papéis

| Papel | Responsabilidade |
|---|---|
| Product Owner técnico | objetivo, escopo, critérios de aceitação |
| Arquiteto / Tech Lead | arquitetura, trade-offs, boundaries, dívida técnica |
| Frontend Engineer | UI, estado, acessibilidade, integração API |
| Backend Engineer | domínio, APIs, serviços, validação e erros |
| Database Engineer | schema, migrações, queries, integridade e rollback |
| QA Engineer | testes, regressões e validação manual |
| Security Reviewer | segredos, auth, autorização e exposição de dados |
| DevOps Engineer | Docker, CI/CD, ambientes, deploy e rollback |
| Technical Writer | README, changelog, ADRs, handoff e PT-PT |
| Repo Maintainer | estrutura, naming, limpeza e dependências |
| Code Reviewer | diff, bugs, simplicidade e manutenibilidade |

## Ativação por risco

- Baixo: implementador + reviewer leve.
- Médio: implementador + QA + writer.
- Alto: PO técnico + arquiteto + implementador + QA + security + reviewer.
- Crítico: adicionar DevOps, rollback explícito e confirmação antes de ações perigosas.

## Resultado esperado

Cada entrega não trivial deve indicar:

- o que foi alterado;
- porquê;
- ficheiros afetados;
- validações executadas;
- limitações;
- riscos restantes;
- próximos passos.
