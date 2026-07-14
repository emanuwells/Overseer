# Cleanup Audit Policy

## Quando Executar

- Antes de concluir tarefas não triviais
- Antes de releases
- Durante auditorias periódicas
- Após refactors grandes

## Checklist de Auditoria

### 1. Git

- [ ] `git status` mostra apenas alterações relevantes
- [ ] Commits com mensagens descritivas
- [ ] Sem commits acidentais de ficheiros grandes
- [ ] Branches limpos

### 2. Ficheiros

- [ ] Sem ficheiros temporários esquecidos
- [ ] Sem código comentado excessivo
- [ ] Imports organizados
- [ ] Sem duplicação de lógica

### 3. Documentação

- [ ] README atualizado se aplicável
- [ ] CHANGELOG atualizado se aplicável
- [ ] Documentos de arquitetura consistentes
- [ ] Sem documentação contraditória

### 4. Testes

- [ ] Testes cobrem código alterado
- [ ] Sem testes quebrados
- [ ] Fixtures limpos

### 5. Segurança

- [ ] Sem secrets expostos
- [ ] Credenciais em env vars
- [ ] Validação de input

## Procedimento

### 1. Diff Review

```bash
git diff --stat
git diff
```

### 2. Ficheiros Temporários

```bash
find . -name "*.tmp" -o -name "*.bak" -o -name "*~"
```

### 3. Imports Não Utilizados

```bash
autoflake --remove-unused-imports -r src/
```

### 4. Verificar Referências

```bash
# Procurar referências a código movido
grep -r "old_module" src/
```

### 5. Testes

```bash
pytest tests/ -v
```

## Registo

Documentar resultados da auditoria em `tasks/lessons.md` ou `docs/ai/ops/EVIDENCE.md`.

## Critérios de Paragem

Parar e reportar se:

- Secrets expostos encontrados
- Testes quebrados
- Importação circular detetada
- Degradação de performance identificada