# CLEANUP_AUDIT_POLICY.md

Política obrigatória para auditoria minuciosa e remoção segura de ficheiros/pastas que não fazem sentido no projeto.

## Objetivo

Manter o repositório pequeno, coerente, pesquisável e livre de lixo técnico.

A IA não deve apenas criar ou alterar ficheiros. Deve também eliminar, depois de auditoria minuciosa, elementos que sejam comprovadamente inúteis, duplicados, obsoletos, temporários ou incoerentes com o projeto.

## Regra principal

Em qualquer iteração não trivial, o agente deve executar uma auditoria de limpeza antes de concluir.

Se, após auditoria, um ficheiro ou pasta for comprovadamente sem função no projeto e seguro de remover, a IA deve removê-lo. Não deve limitar-se a sugerir a remoção.

Se existir dúvida razoável, impacto desconhecido, risco de perda de trabalho do utilizador ou possível ligação a produção/dados/segredos, a IA não deve apagar. Deve listar o item como candidato à remoção e pedir confirmação.

## Auditoria Minuciosa Obrigatória

Antes de apagar, verificar:

1. **Referências internas**  
   Procurar imports, requires, links, scripts, caminhos, docs, CI/CD, Docker, configs, assets e comandos que apontem para o ficheiro/pasta.

2. **Histórico e intenção provável**  
   Distinguir lixo técnico de work-in-progress legítimo, ficheiros do utilizador, backups intencionais, exemplos úteis e documentação de auditoria.

3. **Origem do ficheiro**  
   Priorizar remoção de artefactos criados pela IA, saídas temporárias, duplicados óbvios, builds acidentais e ficheiros vazios sem referências.

4. **Impacto técnico**  
   Confirmar que a remoção não quebra build, testes, documentação, scripts, deploy, Docker, CI/CD, gestores de pacotes ou ferramentas do projeto.

5. **Segurança e dados**  
   Nunca apagar sem confirmação ficheiros que possam conter dados, backups, migrações, logs de auditoria, exportações, `.env` reais, segredos, certificados ou chaves.

6. **Coerência estrutural**  
   Validar contra `AGENTS.md`, `.agents/ops/STRUCTURE.md`, `.agents/policies/NAMING_CONVENTIONS.md`, `README.md`, `COMMANDS.md` e manifestos reais do projeto.

## Deve Remover Sem Confirmação Quando For Inequívoco

- ficheiros temporários criados pela IA na própria iteração;
- pastas vazias sem propósito documentado;
- duplicados exatos sem referência;
- artefactos de build/cache versionados por engano;
- ficheiros `copy`, `old`, `final`, `teste`, `temp` sem uso e sem valor histórico;
- saídas intermédios gerados para uma tarefa e já substituídos por artefacto final;
- documentação substituída, sem referências e sem valor de auditoria;
- configs exemplo duplicadas quando existe modelo canónico equivalente.

## Nunca Remover Sem Confirmação Explícita

- código com possibilidade razoável de ainda ser usado;
- migrações, seeds ou scripts de base de dados;
- backups, dumps, exportações ou dados de utilizador;
- `.env`, certificados, chaves, tokens, configurações reais ou segredos;
- ficheiros alterados pelo utilizador na iteração atual;
- documentação legal, financeira, auditoria, compliance ou histórico;
- assets de marca, imagens, anexos ou ficheiros binários não analisados;
- fluxos de trabalho de CI/CD, Docker, deploy, infra ou produção;
- qualquer item fora do âmbito do pedido cuja função não esteja clara.

## Evidência Obrigatória

Quando houver auditoria de limpeza, registar:

```md
### Auditoria de Limpeza

- **Removidos:** `<path>` — <motivo objetivo>
- **Mantidos:** `<path>` — <motivo objetivo>
- **Candidatos a confirmação:** `<path>` — <risco/dúvida>
- **Verificações feitas:** <imports/links/comandos/estrutura/manifestos>
```

Se nada foi removido, indicar que a auditoria foi feita e que não foram encontrados itens inequivocamente removíveis.

## Relação Com Outras Regras

- `REPO_HYGIENE.md` define a higiene geral.
- Esta política define a obrigação específica de auditoria minuciosa e remoção segura.
- `AGENT_COMPLIANCE.md` torna esta política critério obrigatório em tarefas não triviais.
- `EVIDENCE.md` deve conter o resultado resumido da auditoria.
- `CHANGELOG.md` deve registar remoções versionáveis.
