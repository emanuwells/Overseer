# Stop the Slop

## Objetivo

Remover texto vago, genérico, informal ou enganador de documentação e código.

## O Que É "Slop"

### Texto Vago

| Slop | Substituição |
|---|---|
| "faz coisas" | "executa pipeline" |
| "gerencia" | "cria, lê, atualiza, elimina" |
| "otimizado" | "latência reduzida de X para Y" |
| "melhorado" | "funcionalidade X adicionada" |

### Texto Genérico

| Slop | Substituição |
|---|---|
| "Este projeto faz X" | "Overseer monitoriza pipelines e DAGs externos" |
| "Fácil de usar" | "Configuração em 3 passos" |
| "Muito rápido" | "Resposta em < 100ms" |
| "Seguro" | "Autenticação via JWT, encriptação TLS" |

### Informal

| Slop | Substituição |
|---|---|
| "É fixe" | "Melhora a experiência do utilizador" |
| "Basicamente" | (omitir) |
| "Só" | (omitir) |
| "Tipo" | (omitir) |
| "Tipo de" | "aproximadamente" |

### Enganador

| Slop | Problema | Correção |
|---|---|---|
| "Sempre funciona" | Falso | "Testado em X cenários" |
| "Nunca falha" | Falso | "Taxa de sucesso de 99.9%" |
| "Suporta tudo" | Falso | "Suporta X, Y, Z" |

## Processo de Revisão

### 1. Identificar Slop

Procurar padrões:
- Advérbios vagos: "muito", "bastante", "realmente"
- Adjetivos vagos: "bom", "grande", "pequeno"
- Verbos vagos: "faz", "gerencia", "processa"
- Frases absolutas: "sempre", "nunca", "todo"

### 2. Substituir

Substituir cada instance com:
- Descrição concreta
- Métricas quando aplicável
- Exemplos específicos

### 3. Verificar

- A frase faz sentido?
- É verificável?
- É precisa?

## Exemplos

### Antes

```markdown
Este API é muito rápido e seguro.
```

### Depois

```markdown
O API responde em < 50ms (p95) com autenticação JWT e TLS 1.3.
```

### Antes

```markdown
O sistema gere pipelines de forma eficiente.
```

### Depois

```markdown
O sistema executa até 1000 pipelines concorrentes com rate limiting configurável.