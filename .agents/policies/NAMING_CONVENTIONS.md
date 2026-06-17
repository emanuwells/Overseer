# NAMING_CONVENTIONS.md

Convenções de nomes humanas, profissionais e previsíveis.

## Objetivo

Criar projetos que pareçam mantidos por programadores full-stack sénior: nomes claros, pesquisáveis e coerentes.

## Princípios

- Nomear pela intenção.
- Preferir clareza a abreviações.
- Usar nomes específicos ao domínio.
- Evitar nomes temporários.
- Seguir a convenção da linguagem/framework.
- Escrever documentação em português europeu.
- Usar inglês técnico no código quando esse for o padrão do ecossistema.

## Evitar

```text
teste
teste2
novo
novo_final
final
script
script2
coisas
misc
temp
old
copy
backup
fix
```

## Pastas

Recomendado:

```text
frontend/
backend/
database/
docs/
scripts/
ops/
tests/
fixtures/
config/
src/
```

Não criar pastas sem função clara.

## Ficheiros

Bons exemplos:

```text
sync-external-contacts.ts
validate-environment.php
calculate-monthly-revenue.py
create-user-request.ts
docker-compose.prod.yml
credentials.example.json
```

Maus exemplos:

```text
script1.ts
teste.py
novo.php
final.js
coisas.json
```

## Variáveis E Funções

JavaScript/TypeScript:

```ts
const activeUserId = "";
const pendingInvoices = [];

function calculateMonthlyRevenue() {}
```

Python:

```python
active_user_id = ""
pending_invoices = []

def calculate_monthly_revenue() -> float:
    ...
```

PHP:

```php
$activeUserId = '';
$pendingInvoices = [];

function calculateMonthlyRevenue(): float {}
```

## Booleanos

Boas opções:

```text
isActive
hasPermission
canRetry
shouldSync
wasImported
```

## Scripts

Scripts devem usar ação + alvo:

```text
backup-database.sh
restore-database.sh
sync-production-assets.py
validate-environment.ts
generate-release-notes.py
```

## Endpoints

```text
GET /users
GET /users/:id
POST /projects
PATCH /projects/:id/status
POST /autenticação/login
```

Evitar:

```text
POST /do
GET /data
POST /action
```

## Pergunta Obrigatória

Antes de criar um nome, perguntar:

```text
Este nome explica claramente a intenção daqui a seis meses?
```
