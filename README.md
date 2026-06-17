# Pack de Políticas para Agentes de IA

![Versão](https://img.shields.io/badge/vers%C3%A3o-5.8.1-3498db)
![Estado](https://img.shields.io/badge/estado-stable-2ecc71)
![Licença](https://img.shields.io/badge/licen%C3%A7a-propriet%C3%A1ria-lightgrey)

Pack universal para repositórios profissionais assistidos por IA, com documentação em português europeu.

Foi desenhado para manter projetos simples, limpos, seguros, escaláveis e apresentáveis ao nível de programadores sénior.

## Objetivo

Este pack define:

- regras para IAs em `AGENTS.md`;
- raiz limpa para projetos;
- ficheiros obrigatórios `VERSION` e `LICENSE` na raiz;
- políticas em `.agents/policies/`;
- operação em `.agents/ops/`;
- competências em `.agents/skills/`;
- compatibilidade opcional com Claude em `.claude/skills/`;
- comandos rápidos em `COMMANDS.md`;
- comunicação técnica profissional;
- estrutura de segredos transversal;
- naming humano e profissional;
- higiene iterativa do repositório.

## Estrutura

```text
projeto/
├── AGENTS.md
├── README.md
├── PROJECT_CONTEXT.md
├── COMMANDS.md
├── CHANGELOG.md
├── VERSION
├── LICENSE
├── .env.example
├── .gitignore
├── .agents/
│   ├── policies/
│   ├── ops/
│   └── skills/
├── docs/
├── tasks/
├── scripts/
├── src/ ou frontend/backend/
└── tests/
```

## Instalação

1. Copiar o conteúdo do ZIP para a raiz do projeto.
2. Renomear `PROJECT_CONTEXT.template.md` para `PROJECT_CONTEXT.md`.
3. Usar `.gitignore.template` como base para `.gitignore`.
4. Preencher os campos `A confirmar`.
5. Manter `COMMANDS.md` curto e atualizado.
6. Em projetos com Claude Code, manter `.claude/skills/`.

## Filosofia

- Poucos ficheiros na raiz.
- Políticas fora da raiz.
- Competências específicas, não genéricas.
- Explicações conceptuais e profissionais.
- Menos perguntas ao utilizador, mais decisões seguras.
- Escalabilidade sem burocracia.

## Versão

5.8.1


## MCP

A versão 1.1.0 adiciona uma camada MCP em `.agents/mcp/` com:

- política MCP;
- exemplos genéricos;
- exemplos para Cursor, VS Code e Claude;
- documentação de MCPs core, desenvolvimento, bases de dados e automação de navegador;
- modelos seguros sem segredos.

As configurações reais devem ficar fora do Git quando tiverem tokens, caminhos sensíveis ou credenciais.

## Correção 1.1.1

A versão 1.1.1 reforça a gestão evolutiva de MCPs: a IA pode propor, acrescentar, ajustar ou remover MCPs em modelos/documentação, mas deve pedir confirmação antes de alterar configurações reais com risco, segredos, caminhos sensíveis ou permissões elevadas.


## Versão 1.2.0

A versão 1.2.0 reforça o contrato de conformidade para agentes e adiciona política obrigatória para badges de tecnologias no README.

Inclui:

- `.agents/ops/AGENT_COMPLIANCE.md`;
- `.agents/policies/README_BADGES_POLICY.md`;
- atualização de `AGENTS.md`;
- atualização de `README.template.md` com badges técnicos obrigatórios.


## Correção 1.2.1

A versão 1.2.1 adiciona uma política explícita de auditoria minuciosa e remoção segura.

Inclui:

- `.agents/policies/CLEANUP_AUDIT_POLICY.md`;
- regra obrigatória para apagar ficheiros/pastas comprovadamente inúteis;
- proteção contra remoções ambíguas, sensíveis ou pertencentes ao utilizador;
- evidência obrigatória de removidos, mantidos e candidatos a confirmação.


## Correção 1.2.2

A versão 1.2.2 simplifica o pack final removendo `PACK_AUDIT.md` da raiz.

O histórico de auditoria do pack fica concentrado no `CHANGELOG.md`, evitando ruído nos repositórios criados a partir do modelo.


## Correção 1.2.3

A versão 1.2.3 normaliza a documentação para PT-PT e acrescenta uma política explícita de idioma e acentuação.

Inclui:

- `.agents/policies/LANGUAGE_POLICY.md`;
- regra obrigatória para documentação em português europeu;
- obrigação de acentuação correta em documentação, comentários e textos técnicos;
- preservação de nomes técnicos convencionais, como `README.md`, `CHANGELOG.md`, `.env`, `Dockerfile`, comandos e identificadores de código.


## Correção 1.2.4

A versão 1.2.4 torna obrigatórios os ficheiros `VERSION` e `LICENSE` na raiz do repositório.

Inclui:

- `VERSION` com a versão SemVer atual;
- `LICENSE` com declaração proprietária segura por defeito;
- `.agents/policies/VERSION_LICENSE_POLICY.md`;
- obrigação de manter versão, licença, README, badges, changelog e manifestos coerentes.
