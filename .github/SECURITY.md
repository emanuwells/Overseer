# Segurança

## Reporte

Reportar vulnerabilidades, exposição de segredos ou risco de produção ao responsável do projeto.

## Regras

- Não versionar `.env` reais.
- Não commitar tokens, passwords, chaves SSH, certificados, dumps ou dados pessoais.
- Não publicar logs com segredos.
- Não executar alterações destrutivas em produção sem confirmação explícita.
- Não adicionar dependências de origem desconhecida sem análise.
- Não expor endpoints administrativos sem autenticação e autorização.

## Antes de Deploy

```text
[ ] Segredos fora do Git.
[ ] Variáveis documentadas em `.env.example`.
[ ] Autenticação/autorização revista.
[ ] Logs sem dados sensíveis.
[ ] Rollback conhecido.
[ ] Backup considerado quando há dados.