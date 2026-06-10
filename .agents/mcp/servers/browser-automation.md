# MCP Servers — Browser Automation

MCPs de browser são úteis para validar frontend e fluxos E2E.

## Finalidade

- abrir páginas locais;
- validar UI;
- testar navegação;
- capturar screenshots;
- verificar formulários;
- validar estados loading/error/empty;
- apoio a Lighthouse/Core Web Vitals quando integrado.

## Regras

- preferir local/staging;
- não usar credenciais reais sem necessidade;
- não executar compras, envios, deletes ou ações irreversíveis em produção;
- limpar estado quando necessário;
- documentar fluxos testados.

## Quality Gates Relacionados

- frontend build;
- lint/typecheck;
- testes;
- acessibilidade básica;
- responsividade;
- fluxo principal validado.
