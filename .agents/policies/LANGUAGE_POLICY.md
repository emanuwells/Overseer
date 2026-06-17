# Política de Idioma e Acentuação

Esta política aplica-se a toda a documentação criada, alterada ou revista neste repositório.

## Regra principal

Toda a documentação textual deve estar em **português europeu (PT-PT)** e com **acentuação correta**.

A IA deve corrigir automaticamente, quando for seguro, textos sem acentos, misturas desnecessárias de inglês e português, termos brasileiros evitáveis e frases tecnicamente vagas.

## Âmbito

Aplica-se a:

- `README.md`;
- `CHANGELOG.md`;
- `PROJECT_CONTEXT.md`;
- `COMMANDS.md`;
- documentação em `docs/`;
- políticas em `.agents/policies/`;
- operação em `.agents/ops/`;
- competências em `.agents/skills/` e `.claude/skills/`;
- modelos de issues, pull requests, ADRs, tarefas e handoff;
- comentários em código novo ou alterado, quando o projeto usar comentários em português.

## Exceções permitidas

Podem permanecer em inglês quando forem convenções técnicas, nomes próprios ou identificadores reais:

- nomes de ficheiros: `README.md`, `CHANGELOG.md`, `Dockerfile`, `package.json`;
- nomes de pastas técnicas: `.github`, `.agents`, `.claude`, `src`, `tests`;
- comandos: `npm run build`, `docker compose up`, `git status`;
- APIs, bibliotecas, frameworks, variáveis, classes, funções e endpoints;
- marcas, produtos e protocolos: Docker, GitHub, Node.js, React, MCP, SSH, API, CI/CD;
- termos técnicos sem equivalente natural e universal no contexto do projeto, desde que usados de forma consistente.

## Regras de escrita

A IA deve preferir:

- “ficheiro” em vez de “arquivo”;
- “pasta” em vez de “diretório”, salvo contexto técnico onde “diretório” seja mais preciso;
- “utilizador” em vez de “usuário”;
- “aplicação” em vez de “app”, salvo quando “app” for nome do produto;
- “configuração” em vez de “config”;
- “segredos” em vez de “secrets”, exceto em nomes técnicos;
- “caminhos” em vez de “paths”, exceto em nomes técnicos;
- “critérios de qualidade” em vez de “quality gates”, salvo em contexto de ferramenta que use esse nome;
- “validação” em vez de “check”;
- “autenticação” em vez de “auth”, exceto em identificadores técnicos.

## Acentuação obrigatória

A IA deve corrigir falta de acentos em palavras como:

- não;
- ação, ações;
- configuração;
- validação;
- alteração, alterações;
- documentação;
- técnico, técnica;
- repositório;
- produção;
- execução;
- evidência;
- dependência, dependências;
- decisão, decisões;
- integração;
- autenticação;
- operação;
- segurança;
- informação;
- versão;
- utilizável.

## Antes de concluir

Quando alterar documentação, a IA deve confirmar:

```text
[ ] Documentação escrita em PT-PT.
[ ] Acentuação revista.
[ ] Termos técnicos em inglês mantidos apenas quando forem nomes, comandos, identificadores ou convenções.
[ ] Ausência de mistura desnecessária entre português e inglês.
[ ] README, changelog, políticas e modelos coerentes entre si.
```

## Não conformidade

Se a IA não conseguir rever toda a documentação, deve declarar a limitação, indicar os ficheiros não revistos e não afirmar que a normalização linguística ficou completa.
