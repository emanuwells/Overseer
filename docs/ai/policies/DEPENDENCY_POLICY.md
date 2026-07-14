# Dependency Policy

## Princípios

- Minimizar dependências
- Preferir bibliotecas maduras e mantidas
- Documentar necessidade de cada dependência
- Manter dependências atualizadas

## Quando Adicionar

Adicionar dependência apenas quando:

1. Resolve problema real e comum
2. Não existe solução na stdlib
3. O benefício supera o custo de manutenção
4. A biblioteca é bem mantida

## Não Adicionar

Evitar dependências para:

- Funcionalidade trivial que pode ser implementada
- Funcionalidade já disponível noutra dependência
- Funcionalidade que seria melhor como configuração
- Bibliotecas com histórico de vulnerabilidades

## Gestão de Dependências

### Python

- Usar `requirements.txt` ou `pyproject.toml`
- Fixar versões mínimas, não exatas
- Usar virtualenv ou Poetry/Pipenv
- Documentar propósito de cada dependência principal

### Frontend

- Usar package.json com versões semver
- Preferir bundles pequenos
- Evitar dependências duplicadas

### Docker

- Multi-stage builds para reduzir imagem final
- Usar imagens oficiais quando possível
- Fixar tags de imagem (não `latest`)

## Atualização

### Regular

- Verificar atualizações mensais
- Testar antes de atualizar
- Atualizar uma dependência de cada vez

### Segurança

- Monitorizar CVEs
- Atualizar imediatamente se crítico
- Documentar patches de segurança

## Remoção

Antes de remover:

1. Verificar que não é usada
2. Verificar que não é transitive dependency
3. Testar após remoção
4. Atualizar documentação

## Ferramentas

```bash
# Python - verificar dependências
pip list --outdated

# Python - segurança
pip-audit

# Node - verificar
npm outdated