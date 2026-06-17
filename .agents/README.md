# .agents

Pasta interna com regras, operação e competências para IAs.

## Estrutura

```text
.agents/
├── policies/
├── ops/
└── skills/
```

- `policies/`: regras transversais.
- `ops/`: runbook, critérios de qualidade, handoff e estrutura.
- `skills/`: procedimentos específicos ativados quando relevantes.


## Conformidade e README

- `.agents/ops/AGENT_COMPLIANCE.md` define os critérios obrigatórios antes de concluir uma tarefa.
- `.agents/policies/README_BADGES_POLICY.md` define badges obrigatórios e honestos para READMEs técnicos.
- `.agents/policies/VERSION_LICENSE_POLICY.md` define a presença obrigatória de `VERSION` e `LICENSE` na raiz.


## Limpeza Segura

- `.agents/policies/CLEANUP_AUDIT_POLICY.md` obriga a auditoria minuciosa antes de concluir tarefas não triviais.
- Ficheiros/pastas comprovadamente inúteis e seguros devem ser apagados, não apenas sugeridos.
- Itens ambíguos, sensíveis ou possivelmente pertencentes ao utilizador devem ser listados para confirmação.
