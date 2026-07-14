# Secrets Policy

## Regra Principal

Segredos reais nunca entram no Git.

## Definição de Segredo

Considerar como segredo:

- Tokens de API
- Passwords e credenciais
- Chaves privadas (SSH, GPG)
- Connection strings com credenciais
- Cookies de sessão
- Tokens de acesso (GitHub, AWS, etc.)
- API keys
- Segredos de aplicação

## O Que Pode Ficar No Git

### Exemplos e Templates

- `.env.example` — variáveis sem valores reais
- `*.example.*` — configurações de exemplo
- Ficheiros com `template` no nome
- Documentação de configuração

### Placeholders

Usar placeholders claros:

```
DATABASE_URL=postgresql://user:password@host:port/db
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## O Que Não Pode Ficar No Git

- Ficheiros `.env` com valores reais
- Credenciais hardcoded
- Tokens de produção
- Configurações com caminhos pessoais
- Ficheiros com extensão real de secrets

## Como Gerir Segredos

### Desenvolvimento Local

1. Copiar `.env.example` para `.env`
2. Preencher com valores locais
3. Adicionar `.env` ao `.gitignore`

### Produção

1. Usar variáveis de ambiente
2. Usar secret manager quando disponível
3. Nunca commitar valores reais

### CI/CD

1. Usar secrets do CI/CD provider
2. Passar como variáveis de ambiente
3. Não logging de valores sensíveis

## Deteção

Antes de commit:

```bash
# Verificar segredos comuns
git diff --staged | grep -E "(password|token|secret|key)"

# Usar ferramenta de deteção
git secrets --scan
```

## Se um Segredo For Committed

1. Rodar immediately
2. Revogar o segredo comprometido
3. Gerar novo segredo
4. Atualizar em todos os locais
5. Considerar notificação de segurança