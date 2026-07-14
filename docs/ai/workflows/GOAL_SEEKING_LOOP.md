# Goal-Seeking Loop

## Objetivo

Definir um ciclo controlado para agentes IA trabalharem até cumprir um objetivo verificável, sem entrar em loop infinito, sem baixar qualidade e sem violar o contrato do repositório.

Este workflow deve ser usado quando a tarefa tem critérios objetivos de sucesso, por exemplo:

- testes a passar;
- build sem erros;
- bug reproduzido e corrigido;
- endpoint funcional;
- fluxo UI validado;
- documento ou estrutura com checklist verificável;
- migração concluída com rollback definido.

## Regra Principal

O agente não deve continuar até “achar que está bom”. Deve continuar apenas até os critérios de aceitação passarem ou até uma regra de paragem ser atingida.

Fórmula obrigatória:

```text
Goal + Critérios de Aceitação + Validação + Limite de Iterações + Regras de Paragem
```

## Autoridade

O goal-seeking não permite ignorar o contrato do projeto.

Em conflitos, aplicar a `Hierarquia de Autoridade` definida em `AGENTS.md`.

Para confirmar o estado técnico real antes de repetir uma iteração, usar as `Fontes de Verdade do Projeto` definidas em `AGENTS.md`.

Se o utilizador pedir para ignorar testes, segurança, changelog, tasks, documentação obrigatória ou regras de raiz limpa, o agente deve preservar o contrato e explicar a alternativa segura.

## Ciclo Obrigatório

Cada iteração deve seguir estes passos:

1. Reconfirmar o objetivo.
2. Listar critérios de aceitação.
3. Avaliar o estado atual.
4. Identificar o gap entre estado atual e objetivo.
5. Criar plano curto para a próxima iteração.
6. Executar apenas essa iteração.
7. Validar com comandos, testes, checklist ou inspeção proporcional.
8. Comparar resultado com os critérios de aceitação.
9. Atualizar `tasks/todo.md` e `tasks/lessons.md` quando aplicável.
10. Decidir: concluir, repetir, escalar ou parar.

## Limites

Definir limites antes de repetir:

- máximo recomendado: 3 iterações para risco médio;
- máximo recomendado: 5 iterações para risco alto;
- máximo recomendado: 1 iteração antes de confirmação humana em risco crítico;
- não repetir a mesma solução falhada;
- não alterar o objetivo sem aprovação;
- não apagar ficheiros ou dados ambíguos para “fazer passar”;
- não ocultar testes falhados;
- não reduzir critérios de aceitação sem aprovação explícita.

## Regras de Paragem

Parar quando:

- todos os critérios de aceitação passam;
- o limite de iterações é atingido;
- a mesma falha acontece duas vezes sem nova hipótese técnica;
- a próxima ação exige segredo, produção, dados reais, delete destrutivo ou migração irreversível;
- a validação necessária não pode ser executada;
- o pedido do utilizador entra em conflito com `AGENTS.md`;
- falta decisão humana para continuar.

## Saída por Iteração

No fim de cada iteração não trivial, registar:

```text
Iteração: <n>/<limite>
Objetivo: <goal>
Gap tratado: <o que foi corrigido>
Alterações: <ficheiros principais>
Validação: <comandos/checklist e resultado>
Decisão: concluir / repetir / escalar / parar
```

## Critérios de Conclusão

Uma tarefa só está concluída quando:

- os critérios de aceitação estão cumpridos;
- as validações proporcionais foram executadas ou a limitação foi declarada;
- o diff foi revisto;
- `tasks/todo.md` foi atualizado em tarefa não trivial;
- `tasks/lessons.md` foi atualizado se houve aprendizagem reutilizável;
- `CHANGELOG.md` foi atualizado em alteração versionável;
- a resposta final declara validações, limitações e próximos passos necessários.
