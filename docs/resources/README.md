# Recursos Reutilizáveis

Esta pasta agrupa ficheiros auxiliares que não são documentação operacional direta, mas que servem para criar ou configurar projetos reais.

## Estrutura

```text
docs/resources/
├── examples/
└── templates/
```

## Regras

- `templates/` contém ficheiros base para copiar e adaptar.
- `examples/` contém exemplos fictícios e seguros.
- Não colocar segredos reais nesta pasta.
- Não duplicar documentação que já exista em `docs/ai/`, `docs/architecture/` ou `docs/governance/`.
- Se um template for copiado para a raiz de um projeto real, deve ser preenchido e ajustado ao contexto desse projeto.
