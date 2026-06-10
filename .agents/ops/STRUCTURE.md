# STRUCTURE.md

Estrutura recomendada para projetos limpos, simples e escaláveis.

## Princípio

A raiz deve conter apenas o que humanos e IAs usam com frequência. Regras auxiliares, Skills e operação ficam dentro de `.agents/`.

## Raiz Recomendada

```text
projeto/
├── AGENTS.md
├── README.md
├── PROJECT_CONTEXT.md
├── COMMANDS.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
├── .agents/
├── docs/
├── tasks/
├── scripts/
├── src/ ou frontend/backend/
└── tests/
```

## Estrutura `.agents/`

```text
.agents/
├── README.md
├── policies/
│   ├── PROFESSIONAL_COMMUNICATION.md
│   ├── SECRETS_POLICY.md
│   ├── NAMING_CONVENTIONS.md
│   ├── REPO_HYGIENE.md
│   ├── DEPENDENCY_POLICY.md
│   └── CHANGELOG_POLICY.md
│
├── ops/
│   ├── STRUCTURE.md
│   ├── QUALITY_GATES.md
│   ├── RUNBOOK.md
│   └── HANDOFF.md
│
├── skills/
│   └── <skill>/SKILL.md
└── mcp/
```

## Projeto Simples

```text
projeto/
├── AGENTS.md
├── README.md
├── PROJECT_CONTEXT.md
├── COMMANDS.md
├── CHANGELOG.md
├── .env.example
├── .agents/
├── src/
├── scripts/
└── tests/
```

## Projeto Full-Stack

```text
projeto/
├── AGENTS.md
├── README.md
├── PROJECT_CONTEXT.md
├── COMMANDS.md
├── CHANGELOG.md
├── .env.example
├── .agents/
├── frontend/
├── backend/
├── database/
├── docs/
├── scripts/
├── ops/
├── tests/
└── tasks/
```

## Regras

- Não criar pastas preventivas sem função.
- Não espalhar policies na raiz.
- Manter `COMMANDS.md` na raiz por acesso rápido.
- Manter `README.md` como apresentação profissional do projeto.
- Manter `PROJECT_CONTEXT.md` como contexto técnico específico.


## Estrutura MCP

```text
.agents/mcp/
├── README.md
├── MCP_POLICY.md
├── mcp.example.json
├── cursor.mcp.example.json
├── vscode.mcp.example.json
├── claude.mcp.example.json
├── servers/
└── templates/
```

A pasta `.agents/mcp/` contém exemplos seguros. Configurações reais com secrets ficam fora do Git.
