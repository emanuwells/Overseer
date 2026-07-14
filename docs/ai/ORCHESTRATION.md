# Orquestração da Equipa IA

## Objetivo

Definir como coordenar agentes, subagentes, skills, workflows e revisões para que um programador solo consiga operar como uma equipa sénior full stack sem perder controlo técnico.

Este documento não substitui `AGENTS.md`. Ele transforma as regras do contrato principal num processo de decisão: quem entra, quando entra, em que ordem, que contexto lê, que evidência entrega e quando deve parar.

## Princípios

- Um agente coordenador deve existir em qualquer tarefa média, alta ou crítica.
- O coordenador não deve implementar tudo por impulso; deve encaminhar trabalho para papéis, workflows e skills relevantes.
- Cada papel deve receber apenas o contexto necessário para a sua responsabilidade.
- A execução deve ser faseada, auditável, reversível e validada.
- Em caso de conflito, aplicar a `Hierarquia de Autoridade` definida em `AGENTS.md`.
- Para confirmar o estado técnico real, usar as `Fontes de Verdade do Projeto` definidas em `AGENTS.md`.
- O pedido do utilizador define o objetivo, mas não pode anular qualidade, segurança, validação, registo, raiz limpa ou critérios de paragem.

## Papel do Orquestrador

O orquestrador é o papel de coordenação. Pode ser executado pela mesma IA que implementa, mas deve separar mentalmente as decisões de coordenação das decisões de implementação.

Responsabilidades:

1. classificar o pedido;
2. classificar risco;
3. escolher documentos a ler;
4. escolher papéis necessários;
5. escolher workflow e skills aplicáveis;
6. decidir se o objetivo exige goal-seeking loop;
7. dividir em fases;
8. definir validações;
9. controlar handoff entre papéis;
10. bloquear ações perigosas;
11. garantir registo em `tasks/`, `CHANGELOG.md` e documentação relevante.

## Quando Usar

| Situação | Orquestração |
|---|---|
| Alteração textual simples | opcional |
| Bugfix local | leve |
| Feature média | obrigatória |
| Refactor estrutural | obrigatória |
| Backend, DB, auth, CI/CD, deploy | obrigatória |
| Produção, segredos, migrações irreversíveis | obrigatória + confirmação explícita |

## Fluxo de Orquestração

### 1. Intake

Determinar:

- objetivo real;
- tipo de tarefa: feature, bugfix, refactor, docs, DevOps, dados, segurança ou revisão;
- risco: baixo, médio, alto ou crítico;
- ficheiros ou módulos prováveis;
- comandos de validação;
- restrições do utilizador.

Documentos mínimos:

- `AGENTS.md`;
- `PROJECT_CONTEXT.md`, se existir;
- `COMMANDS.md`, se existir;
- `tasks/todo.md`;
- `tasks/lessons.md`;
- `docs/ai/policies/CONTEXT_BUDGET_POLICY.md`.

### 2. Routing

Escolher papéis conforme a tarefa:

| Tipo de tarefa | Papéis mínimos |
|---|---|
| Feature UI | Product Owner técnico, Frontend Engineer, QA, Code Reviewer |
| Feature API | Product Owner técnico, Backend Engineer, QA, Security Reviewer, Code Reviewer |
| Full stack | Product Owner técnico, Arquiteto, Frontend, Backend, QA, Security, Code Reviewer |
| Base de dados | Database Engineer, Backend Engineer, QA, Security, DevOps se houver deploy |
| Refactor | Arquiteto, Repo Maintainer, QA, Code Reviewer, Technical Writer |
| Bugfix | Implementador do domínio, QA, Code Reviewer |
| CI/CD ou Docker | DevOps, Security, QA, Technical Writer |
| Documentação | Technical Writer, Code Reviewer técnico |
| Segurança | Security Reviewer, Backend/DevOps conforme impacto, Code Reviewer |

### 3. Seleção de Workflow

Usar apenas um workflow primário:

| Pedido | Workflow |
|---|---|
| Nova funcionalidade | `docs/ai/workflows/10-feature-delivery.md` |
| Refactor | `docs/ai/workflows/20-safe-refactor.md` |
| Bug | `docs/ai/workflows/30-bugfix.md` |
| Revisão | `docs/ai/workflows/40-quality-review.md` |
| Release/handoff | `docs/ai/workflows/50-release-handoff.md` |
| Entrada ambígua | `docs/ai/workflows/00-intake.md` |
| Objetivo verificável com repetição | `docs/ai/workflows/GOAL_SEEKING_LOOP.md` |

`GOAL_SEEKING_LOOP.md` pode ser usado em conjunto com o workflow primário quando houver critérios objetivos de aceitação. Ele controla iterações, validação, repetição e paragem; não substitui o contrato de `AGENTS.md`.

### 4. Seleção de Skills

Ativar skills apenas quando forem diretamente úteis.

Exemplos:

- `safe-refactor` para refactors multi-ficheiro;
- `bugfix-diagnostics` para falhas, crashes e regressões;
- `quality-gate-runner` para validar antes de fechar;
- `database-migration-safety` para schema e migrações;
- `secrets-layout-guardian` para `.env`, chaves e credenciais;
- `repo-hygiene` para limpeza estrutural;
- `professional-documentation` para README, manuais e handoff.

Não carregar todas as skills por defeito.

### 5. Plano

Para risco médio, alto ou crítico, o plano deve conter:

- objetivo;
- fora de escopo;
- fases;
- ficheiros afetados;
- papéis envolvidos;
- validações por fase;
- rollback;
- critérios de conclusão;
- pontos que exigem confirmação humana.

Quando existir goal-seeking, o plano também deve definir:

- limite de iterações;
- critérios de aceitação mensuráveis;
- validações obrigatórias;
- condições para repetir;
- condições para parar ou escalar.

### 6. Execução

Regras:

- executar uma fase de cada vez;
- não misturar responsabilidades;
- não avançar para fase seguinte se validação falhar sem causa conhecida;
- preservar comportamento existente salvo pedido contrário;
- preferir alterações pequenas, legíveis e reversíveis;
- registar decisões relevantes.

### 7. Review Cruzada

Antes de concluir tarefas médias, altas ou críticas, simular revisão por:

- QA Engineer: regressões, edge cases e validação;
- Security Reviewer: segredos, auth, autorização, exposição de dados;
- Code Reviewer: simplicidade, duplicação, bugs e manutenibilidade;
- Technical Writer: documentação, changelog, handoff e comandos.

### 8. Fecho

Antes da resposta final:

- rever diff;
- executar validações possíveis;
- atualizar `tasks/todo.md`;
- atualizar `tasks/lessons.md` se houver aprendizagem reutilizável;
- atualizar `CHANGELOG.md` se a alteração for versionável;
- atualizar documentação se mudou uso, arquitetura, comandos ou processo.

## Contrato de Handoff Entre Papéis

Cada papel deve entregar informação curta e verificável.

Formato recomendado:

```text
Papel: <nome>
Objetivo: <responsabilidade nesta fase>
Entradas: <ficheiros/documentos lidos>
Decisões: <decisões tomadas>
Alterações: <ficheiros ou módulos afetados>
Validação: <comandos/resultados ou limitação>
Riscos: <riscos restantes>
Próximo papel: <se aplicável>
```

## Padrões de Orquestração

### Padrão A — Implementação simples

1. Product Owner técnico define critério.
2. Engineer implementa.
3. QA valida.
4. Code Reviewer fecha.
5. Technical Writer atualiza registos, se necessário.

### Padrão B — Refactor seguro

1. Arquiteto mapeia estrutura atual.
2. Repo Maintainer identifica ficheiros e limpeza.
3. Engineer executa fase mínima.
4. QA valida comportamento.
5. Code Reviewer audita diff.
6. Technical Writer atualiza documentação.

### Padrão C — Full stack

1. Product Owner técnico define escopo.
2. Arquiteto define fronteiras.
3. Backend/Database implementam contrato e persistência.
4. Frontend integra.
5. QA valida fluxo completo.
6. Security revê dados e permissões.
7. DevOps valida build/deploy se aplicável.
8. Code Reviewer fecha.

### Padrão D — Incidente/bug crítico

1. Orquestrador congela escopo.
2. Bugfix Diagnostics reproduz ou isola causa.
3. Engineer aplica correção mínima.
4. QA valida regressão.
5. Security/DevOps revê impacto se aplicável.
6. Technical Writer regista causa, correção e prevenção.

## Critérios de Paragem

Parar e pedir confirmação quando:

- for necessário apagar dados, ficheiros críticos ou histórico;
- houver alteração de schema irreversível;
- houver impacto em produção;
- surgirem segredos reais;
- uma dependência nova for necessária mas não estiver justificada;
- a validação falhar e a causa não for entendida;
- o pedido real divergir do plano inicial.

## Anti-Padrões

Evitar:

- um único agente agir como “faz tudo” sem plano;
- carregar toda a pasta `docs/ai/` sem necessidade;
- usar múltiplos adaptadores ao mesmo tempo;
- criar documentação longa sem ligação ao código;
- fazer refactor e feature no mesmo commit sem justificação;
- declarar revisão, testes ou validação que não foram executados;
- deixar tarefas sem registo em `tasks/`.

## Saída Final Esperada

Para tarefas não triviais, a resposta final deve indicar:

- objetivo concluído;
- papéis efetivamente usados;
- ficheiros principais alterados;
- validações executadas;
- riscos ou limitações;
- registos atualizados;
- próximo passo apenas se for necessário.
