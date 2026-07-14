# Professional Communication Policy

## Objetivo

Garantir que a comunicação da IA é clara, profissional e adequada para audiências técnicas.

## Princípios

### Clareza

- Explicar o quê e porquê, não apenas o quê
- Usar linguagem técnica precisa
- Evitar jargão desnecessário
- Fornecer contexto quando relevante

### Profissionalismo

- Tratar o projeto como trabalho profissional
- Documentar decisões técnicas
- Explicar trade-offs quando aplicável
- Ser honesto sobre limitações

### Precisão Técnica

- Usar termos técnicos corretamente
- Referenciar código real, não documentação
- Especificar versões e configurações
- Incluir exemplos quando útil

## Linguagem a Evitar

### Frases Proibidas

| Evitar | Preferir |
|---|---|
| "Isto liga à DB" | "Este módulo persiste dados em PostgreSQL" |
| "O API vai buscar ao storage" | "A API recupera artefactos do storage S3" |
| "O sistema faz X" | "O componente Y implementa X" |
| "É fixe" | "Melhora a experiência do utilizador" |
| "Basicamente" | (omitir ou usar termo técnico) |
| "Só" | (omitir ou usar termo técnico) |

### Frases Vagas

| Evitar | Preferir |
|---|---|
| "Melhorar performance" | "Reduzir latência de resposta de 500ms para 100ms" |
| "Otimizar queries" | "Indexar coluna created_at para queries por data" |
| "Corrigir bug" | "Corrigir race condition em concurrent writes" |

## Estrutura de Resposta

### Para Explicações Técnicas

1. **Contexto**: O que é e por que existe
2. **Comportamento**: Como funciona atualmente
3. **Impacto**: O que muda com a alteração
4. **Alternativas**: Se há outras abordagens consideradas

### Para Entregas

1. **Resumo**: O que foi feito
2. **Ficheiros**: Lista dos alterados
3. **Validações**: Testes executados e resultados
4. **Limitações**: O que não foi feito ou pode não funcionar
5. **Próximos passos**: Se aplicável

## Documentação de Arquitetura

A documentação deve ser adequada para:

- Equipa técnica atual
- Recrutadores ou clientes
- Futuros maintainers
- Revisores de código

Evitar:

- Explicações excessivamente internas
- Referências a ferramentas pessoais
-piadas ou humor inapropriado
- Termos depreciativos