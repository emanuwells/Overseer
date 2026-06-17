# Política de VERSION e LICENSE

Esta política aplica-se sempre que um agente criar, alterar, rever ou preparar uma entrega de repositório.

## Regra principal

A raiz do repositório deve conter sempre:

- `VERSION` — versão atual do projeto em SemVer;
- `LICENSE` — licença explícita do projeto ou declaração proprietária clara.

Estes ficheiros são obrigatórios. Não devem ser removidos por limpeza automática, mesmo que o projeto seja pequeno.

## VERSION

O ficheiro `VERSION` deve conter apenas uma linha com a versão SemVer atual:

```text
0.1.0
```

Regras:

- usar SemVer: `MAJOR.MINOR.PATCH`;
- iniciar projetos novos em `0.1.0`, salvo instrução explícita diferente;
- manter `VERSION`, badges do README, `CHANGELOG.md` e manifestos coerentes quando houver alteração de versão;
- não usar texto adicional no ficheiro `VERSION`;
- não inventar versão se existir uma versão formal noutro manifesto sem a reconciliar.

## LICENSE

O ficheiro `LICENSE` deve declarar claramente o regime de utilização do projeto.

Regras:

- não escolher licença open-source sem instrução explícita do titular do projeto;
- se a licença ainda não estiver definida, usar declaração proprietária segura com placeholders claros;
- se o projeto for open-source, usar o texto oficial da licença escolhida, sem adaptações informais;
- manter o badge de licença no `README.md` coerente com o conteúdo de `LICENSE`;
- verificar compatibilidade da licença com dependências externas quando o projeto for distribuído;
- não apagar `LICENSE` durante auditoria de limpeza.

## Boas práticas

- Para projetos privados: usar declaração proprietária explícita, por exemplo “Todos os direitos reservados”.
- Para projetos open-source: usar identificador SPDX conhecido no README, quando aplicável.
- Para packages publicados: alinhar `LICENSE` com `package.json`, `pyproject.toml`, `composer.json`, `.csproj` ou manifesto equivalente.
- Para templates: manter placeholders claros e obrigar substituição antes de publicação.

## Critério antes de concluir

Antes de marcar uma tarefa como concluída, o agente deve confirmar:

```text
[ ] Existe `VERSION` na raiz.
[ ] `VERSION` contém uma versão SemVer válida.
[ ] Existe `LICENSE` na raiz.
[ ] O README reflete a versão e licença corretas quando contém badges.
[ ] O CHANGELOG está coerente com a versão quando houve alteração versionável.
[ ] A licença não foi alterada sem autorização explícita quando isso muda direitos de uso.
```
