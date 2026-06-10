# SECRETS_POLICY.md

Estrutura transversal para segredos, SSH, `.env` e credenciais.

## Regra Principal

Segredos reais nunca devem ser versionados.

A IA deve tratar como sensível:

- chaves privadas SSH;
- tokens;
- passwords;
- cookies;
- certificados;
- ficheiros `.env` reais;
- strings de ligação;
- JSON de service accounts;
- dumps de base de dados com dados reais.

## Ordem Recomendada

1. SSH configurado fora do repositório.
2. Variáveis de ambiente.
3. Secret manager/plataforma de deploy.
4. JSON de credenciais apenas quando o serviço exigir.
5. Ficheiros locais ignorados pelo Git.

## Estrutura Recomendada

```text
projeto/
├── .env.example
├── .gitignore
├── secrets/
│   ├── README.md
│   └── examples/
│       ├── credentials.example.json
│       └── ssh-config.example
└── .secrets/              # ignorado pelo Git
    ├── ssh/
    ├── env/
    └── credentials/
```

## Pode Ser Versionado

- `.env.example`;
- `secrets/README.md`;
- `secrets/examples/*.example.json`;
- `secrets/examples/ssh-config.example`;
- nomes de variáveis;
- documentação de configuração sem valores reais.

## Nunca Versionar

- `.env`;
- `.env.local`;
- `.env.production`;
- `.secrets/**`;
- `*.pem`;
- `*.key`;
- `*.p12`;
- `*.pfx`;
- JSON real de service accounts;
- backups e dumps com dados reais.

## `.gitignore` Base

```gitignore
.env
.env.*
!.env.example

.secrets/
.secrets/**

*.pem
*.key
*.p12
*.pfx
*service-account*.json
*credentials*.json

!*.example.json
!secrets/
!secrets/README.md
!secrets/examples/
!secrets/examples/*.example.json
!secrets/examples/*.example
```

## SSH

SSH deve ficar fora do repositório.

A IA pode sugerir validação:

```bash
ssh -T git@github.com
git remote -v
```

A IA não pode imprimir, copiar, criar, substituir ou apagar chaves SSH sem autorização explícita.

## JSON De Credenciais

JSON real só deve existir quando inevitável.

Regras:

- usar `*.example.json` no Git;
- guardar JSON real em `.secrets/credentials/` localmente;
- em produção, preferir secret manager;
- nunca imprimir o conteúdo real.

## Checklist

```text
[ ] Nenhum segredo real versionado.
[ ] `.env.example` usa valores fictícios.
[ ] JSON de credenciais é exemplo.
[ ] SSH fica fora do repositório.
[ ] `.gitignore` protege secrets.
```
