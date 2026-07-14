# AGENTS.md

Contrato operacional para agentes e ferramentas de IA que trabalhem neste repositório.

## Prioridades

1. Segurança, lei e regras da plataforma.
2. Este contrato.
3. Código e testes versionados.
4. Documentação de arquitetura e operação.
5. Pedido do utilizador.

Quando documentação e código divergirem, o código e os testes descrevem o estado atual. Corrija a documentação ou peça confirmação antes de alterar comportamento.

## Leitura mínima

Antes de tarefas não triviais, leia `PROJECT_CONTEXT.md`, `COMMANDS.md`, `docs/ai/DAILY_AGENT_WORKFLOW.md`, `docs/ai/policies/CONTEXT_BUDGET_POLICY.md`, `tasks/todo.md` e `tasks/lessons.md`. Abra apenas políticas e documentos diretamente relacionados com a tarefa.

## Regras obrigatórias

- Preserve alterações existentes do utilizador.
- Verifique o estado Git antes de mudanças relevantes.
- Não versionar segredos, catálogos reais, IPs, nomes pessoais ou caminhos privados.
- Não apagar dados, backups, migrações ou produção sem confirmação explícita.
- Não misturar feature, correção, refactor e limpeza sem declarar o motivo.
- Não introduzir dependências sem justificar necessidade e alternativa.
- Não declarar validações que não foram executadas.
- Atualizar `tasks/todo.md` em trabalho não trivial, `tasks/lessons.md` quando houver aprendizagem reutilizável e `CHANGELOG.md` em alterações versionáveis.
- Escrever documentação em português europeu; utilizar inglês técnico em identificadores e contratos de código.

## Risco e execução

- Baixo: documentação curta ou ajuste local; revisão leve.
- Médio: scripts, componentes e endpoints simples; plano curto e testes.
- Alto: backend, base de dados, Docker ou refactor multi-ficheiro; execução faseada e rollback.
- Crítico: produção, SSH, segredos, histórico Git ou operações destrutivas; backup verificável e confirmação explícita.

Para risco médio ou superior: descobrir, planear, executar em incrementos, validar, rever o diff e registar o resultado. Pare perante falhas sem causa entendida.

## Estrutura e configuração privada

A raiz deve conter apenas ficheiros de projeto e as pastas `.github/`, `deploy/`, `docker/`, `docs/`, `frontend/`, `openapi/`, `runtime/`, `scripts/`, `secrets/`, `src/`, `tasks/` e `tests/`.

Configuração real de runners fica fora do Git e é selecionada por `OVERSEER_RUNNERS_DIR`. Segredos ficam em `.env`, gestor de segredos ou ficheiros locais ignorados.

## Validação e entrega

Use os comandos reais de `COMMANDS.md`. Antes de concluir, reveja o diff, referências, imports, documentação, ficheiros temporários e exposição de dados. A resposta final deve listar resumo, ficheiros principais, validações executadas, limitações e próximos passos necessários.
