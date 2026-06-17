# SECRETS_POLICY.md

Estrutura transversal para segredos, SSH, `.env` e credenciais.

## Regra principal

Segredos reais nunca devem ser versionados.

A IA deve tratar como sensível:

- chaves privadas SSH;
- tokens;
- passwords;
- cookies;
- certificados;
- ficheiros `.env` reais;
- strings de ligação;
- JSON de contas de serviço;
- dumps de base de dados com dados reais.

## Ordem recomendada

1. SSH configurado fora do repositório.
2. Variáveis de ambiente.
3. Gestor de segredos/plataforma de deploy.
4. JSON de credenciais apenas quando o serviço exigir.
5. Ficheiros locais ignorados pelo Git.

## Estrutura recomendada

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

## Pode ser versionado

- `.env.example`;
- `secrets/README.md`;
- `secrets/examples/*.example.json`;
- `secrets/examples/ssh-config.example`;
- nomes de variáveis;
- documentação de configuração sem valores reais.

## Nunca versionar

- `.env`;
- `.env.local`;
- `.env.production`;
- `.secrets/**`;
- `*.pem`;
- `*.key`;
- `*.p12`;
- `*.pfx`;
- JSON real de contas de serviço;
- backups e dumps com dados reais.

## `.gitignore` base

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

## JSON de credenciais

JSON real só deve existir quando inevitável.

Regras:

- usar `*.example.json` no Git;
- guardar JSON real em `.secrets/credentials/` localmente;
- em produção, preferir gestor de segredos;
- nunca imprimir o conteúdo real.

## Checklist

```text
[ ] Nenhum segredo real versionado.
[ ] `.env.example` usa valores fictícios.
[ ] JSON de credenciais é exemplo.
[ ] SSH fica fora do repositório.
[ ] `.gitignore` protege segredos.
```
