# AGENTS.md

Contrato operacional obrigatório para qualquer IA, agente, IDE assistido por IA ou ferramenta autónoma que trabalhe neste repositório.

Este projeto deve ser tratado como trabalho profissional mantido por um programador solo com apoio de uma equipa IA sénior full stack. O objetivo é entregar alterações úteis, seguras, reversíveis, testáveis e bem documentadas.

## Hierarquia de Autoridade

A hierarquia de autoridade resolve conflitos entre instruções. O pedido do utilizador define o objetivo da tarefa, mas não pode sobrepor-se ao contrato técnico deste repositório.

1. Regras superiores de segurança, sistema, plataforma e lei aplicável.
2. Este `AGENTS.md`.
3. Documentos normativos relevantes em `docs/ai/`, `docs/architecture/` e `docs/ai/ops/`.
4. `PROJECT_CONTEXT.md`, quando existir.
5. `COMMANDS.md`.
6. Pedido atual do utilizador.
7. Convenções reais do código existente.
8. Adaptador ativo da ferramenta, se existir.

Se o pedido do utilizador entrar em conflito com este contrato, preservar o contrato, explicar o conflito e propor uma alternativa segura.

## Fontes de Verdade do Projeto

As fontes de verdade descrevem como o projeto funciona de facto. Servem para confirmar realidade técnica, não para resolver conflitos de autoridade.

1. Código real versionado.
2. Testes reais e respetivos resultados.
3. Configurações reais de runtime, build, CI/CD e deploy.
4. Manifestos e lockfiles de dependências.
5. `COMMANDS.md`, quando atualizado.
6. `PROJECT_CONTEXT.md`, quando existir.
7. `docs/architecture/` e ADRs.
8. `README.md` e documentação de uso.

Se documentação e código real divergirem, assumir que o código real descreve o estado atual. Corrigir a documentação ou pedir confirmação antes de alterar comportamento.

Adaptadores de IDE/agente são opcionais e vivem em `tools/ai-adapters/`. Nunca devem substituir o núcleo neutro do repositório.

## Leitura Mínima Obrigatória

Antes de tarefas não triviais:

1. Ler `AGENTS.md`.
2. Ler `PROJECT_CONTEXT.md`, se existir.
3. Ler `COMMANDS.md`, se existir.
4. Ler `docs/ai/DAILY_AGENT_WORKFLOW.md`.
5. Ler `docs/ai/policies/CONTEXT_BUDGET_POLICY.md`.
6. Ler `docs/ai/ORCHESTRATION.md` em tarefas médias, altas, críticas ou multi-papel.
7. Ler `docs/ai/workflows/GOAL_SEEKING_LOOP.md` quando o objetivo tiver critérios verificáveis.
8. Ler `tasks/todo.md` e `tasks/lessons.md`.
9. Abrir apenas os documentos adicionais estritamente relevantes para a tarefa.
10. Em tarefas de risco médio, alto ou crítico, consultar antes de agir os documentos relevantes em `docs/ai/`, `docs/architecture/` e `docs/ai/ops/`, sem carregar contexto desnecessário.

## Raiz Limpa

A raiz deve ser curta, previsível e sénior.

Permitido na raiz:

- `README.md`, `AGENTS.md`, `COMMANDS.md`, `CHANGELOG.md`;
- `PROJECT_CONTEXT.md`, quando preenchido para um projeto real;
- `VERSION`, `LICENSE`;
- `.gitattributes`, `.gitignore`;
- `.github/`, `deploy/`, `docker/`, `docs/`, `frontend/`, `openapi/`, `runtime/`, `scripts/`, `secrets/`, `src/`, `tasks/`, `tests/`, `tools/`.

Fora da raiz por defeito:

- `PROJECT_CONTEXT.template.md` vive em `docs/resources/templates/PROJECT_CONTEXT.template.md`;
- `.env.example` vive em `docs/resources/templates/.env.example`;
- `.gitignore.template` vive em `docs/resources/templates/.gitignore.template`;
- `CONTRIBUTING.md` vive em `docs/governance/CONTRIBUTING.md`;
- `SECURITY.md` vive em `.github/SECURITY.md`.

Não manter adaptadores ativos na raiz por defeito. Ativar apenas quando necessário com `scripts/activate-ai-adapter.*` e remover com `scripts/deactivate-ai-adapter.*`.

## Regras Absolutas

- Preservar alterações existentes do utilizador.
- Verificar estado Git antes de alterações médias, altas ou críticas, quando possível.
- Não apagar ficheiros ambíguos, dados, segredos, backups, migrações ou produção sem confirmação explícita.
- Não misturar feature, bugfix, refactor e limpeza estrutural sem declarar o motivo.
- Não alterar comportamento funcional sem explicar impacto.
- Não introduzir dependências sem justificar necessidade, risco e alternativa.
- Não versionar segredos reais.
- Em repositórios públicos, desactivar nos settings do Cursor a atribuição de co-autor em commits do Agent; não incluir `Co-authored-by: Cursor` em mensagens de commit.
- Não declarar testes, lint, build, deploy ou validações que não foram executados.
- Não concluir trabalho não trivial sem atualizar `tasks/todo.md`.
- Atualizar `tasks/lessons.md` quando houver aprendizagem reutilizável.
- Atualizar `CHANGELOG.md` em alterações versionáveis.
- Manter documentação em português europeu com acentuação correta, exceto nomes técnicos, comandos e identificadores.

## Classificação de Risco

| Risco | Exemplos | Obrigatório |
|---|---|---|
| Baixo | texto curto, README, ajuste local | alteração direta e validação leve |
| Médio | script, componente, endpoint simples, config local | plano curto, diff controlado, validação, registo |
| Alto | backend, auth, DB, Docker, CI/CD, refactor multi-ficheiro | plano faseado, validação por fase, rollback, handoff |
| Crítico | produção, SSH real, segredos, delete destrutivo, migrações irreversíveis | confirmação explícita antes da ação perigosa |

## Fluxo Operacional

### 1. Descobrir

- Identificar stack por manifestos, estrutura e comandos.
- Mapear ficheiros afetados.
- Ler arquitetura em `docs/architecture/` quando existir.
- Consultar `tasks/lessons.md`.
- Classificar risco.

### 2. Planear

Obrigatório para risco médio, alto ou crítico.

O plano deve conter objetivo, escopo, fora de escopo, ficheiros afetados, validações, rollback e critérios de conclusão.

Para objetivos verificáveis, usar `docs/ai/workflows/GOAL_SEEKING_LOOP.md`: planear, executar, validar, rever e repetir até cumprir critérios de aceitação ou atingir uma regra de paragem.

### 3. Executar

- Alterar uma área de cada vez.
- Preferir mudanças pequenas, legíveis e reversíveis.
- Respeitar padrões existentes.
- Evitar overengineering.
- Atualizar documentação junto da alteração.

### 4. Validar

Executar comandos reais de `COMMANDS.md` quando existirem. Se não existirem, fazer validação proporcional e declarar a limitação.

### 5. Auditar

Antes de concluir tarefas não triviais:

- rever diff;
- procurar ficheiros temporários ou inúteis;
- confirmar imports, referências, scripts, docs e CI/CD;
- listar candidatos ambíguos em vez de apagar sem segurança.

### 6. Registar

Atualizar conforme aplicável:

- `tasks/todo.md` em cada iteração não trivial;
- `tasks/lessons.md` para aprendizagem reutilizável;
- `CHANGELOG.md` em alterações versionáveis;
- `README.md`, `COMMANDS.md` ou `docs/architecture/` quando instalação, execução, arquitetura ou comandos mudarem;
- `docs/ai/ops/HANDOFF.md` quando houver continuidade.

## Modelo de Equipa IA

Para tarefas médias, altas, críticas ou multi-papel, usar `docs/ai/ORCHESTRATION.md` para decidir papéis, sequência, handoff, validações e critérios de paragem.

Ativar apenas os papéis relevantes ao risco:

| Papel | Responsabilidade |
|---|---|
| Product Owner técnico | objetivo, escopo, critérios de aceitação |
| Arquiteto | limites, módulos, decisões, trade-offs |
| Frontend Engineer | UI, estado, acessibilidade, performance, integração API |
| Backend Engineer | domínio, API, validação, erros, logs, segurança |
| Database Engineer | schema, migrações, integridade, performance, rollback |
| QA Engineer | testes, regressões, edge cases, validação manual |
| Security Reviewer | segredos, auth, autorização, exposição de dados |
| DevOps Engineer | build, Docker, CI/CD, ambiente, deploy, rollback |
| Technical Writer | README, docs, changelog, handoff |
| Repo Maintainer | estrutura, limpeza, naming, dependências |
| Code Reviewer | diff, bugs, simplicidade, regressões |

## Refactors

Refactor estrutural exige plano antes de código.

Obrigatório:

- preservar comportamento;
- separar por fases;
- não misturar com feature;
- validar por fase;
- manter rollback claro;
- atualizar imports, testes e documentação;
- parar se validações falharem sem causa entendida.

Usar `docs/ai/policies/SAFE_REFACTOR_POLICY.md` e `docs/ai/skills/safe-refactor/SKILL.md` quando aplicável.

## Qualidade

Preferir código simples, explícito, modular, testável e documentado onde importa.

Evitar:

- ficheiros gigantes;
- abstrações sem uso real;
- duplicação de regras entre ferramentas;
- dependências sem retorno claro;
- comentários que apenas repetem o código;
- alterações cosméticas misturadas com lógica.

## Segurança

- Segredos reais nunca entram no Git.
- Logs não devem expor tokens, passwords, cookies, chaves privadas ou dados pessoais desnecessários.
- Produção, SSH, permissões, backups e migrações destrutivas exigem cuidado proporcional e confirmação quando houver risco irreversível.

## Resposta Final do Agente

Para trabalho executado, responder com:

- resumo objetivo;
- ficheiros principais alterados;
- validações executadas e resultado;
- limitações conhecidas;
- próximos passos, apenas se forem necessários.
