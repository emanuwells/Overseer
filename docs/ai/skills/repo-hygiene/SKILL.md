# Repository Hygiene

## Objetivo

Auditar e remover com segurança ficheiros desnecessários, mantendo o repositório limpo e organizado.

## Quando Usar

- Antes de releases
- Após refactors
- Durante auditorias
- Limpeza periódica

## Checklist de Auditoria

### 1. Git Status

```bash
git status
git status --porcelain
```

Verificar:
- [ ] Apenas ficheiros relevantes
- [ ] Sem ficheiros grandes acidentais
- [ ] Sem secrets

### 2. Ficheiros Temporários

```bash
# Python
find . -name "__pycache__" -type d
find . -name "*.pyc"
find . -name "*.pyo"
find . -name ".pytest_cache"

# Node
find . -name "node_modules"

# OS
find . -name ".DS_Store"
find . -name "Thumbs.db"
```

### 3. Imports Não Utilizados

```bash
autoflake --remove-unused-imports -r src/
```

### 4. Código Morto

```bash
vulture src/ --min-confidence 80
```

### 5. .gitignore

```bash
# Verificar se cobre tudo
cat .gitignore
```

## Remoção Segura

### Regra de Ouro

**Nunca apagar sem verificar:**

1. O ficheiro existe no working directory
2. Não está em uso por outros ficheiros
3. Não é necessário para produção
4. Não contém dados únicos

### Ficheiros Seguros de Remover

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `node_modules/` (se não versionado)
- `*.log`
- Backups locais

### Ficheiros Candidatos (Verificar Primeiro)

- Código comentado
- Imports não utilizados
- Funções não chamadas
- Ficheiros aparentemente duplicados

### Nunca Remover

- Código de produção
- Testes
- Configuração real
- Documentação
- Ficheiros com histórico único

## Processo

1. Executar auditoria
2. Listar candidatos
3. Verificar cada um
4. Remover com segurança
5. Testar após remoção
6. Commit com mensagem descritiva