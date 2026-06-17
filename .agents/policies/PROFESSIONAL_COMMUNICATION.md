# PROFESSIONAL_COMMUNICATION.md

Política de comunicação, documentação e explicação técnica.

## Objetivo

Garantir que o projeto é explicado como um repositório profissional, apresentável e escalável, ao nível de um programador sénior.

## Regra principal

Explicar conceitos, responsabilidades e decisões técnicas. Evitar descrições demasiado internas, frágeis ou casuais.

## Mau Exemplo

```text
Isto liga à DB MAIATRON e vai buscar os dados.
```

## Bom Exemplo

```text
A camada de persistência centraliza o acesso à base de dados relacional e expõe operações de leitura/escrita através de serviços reutilizáveis, mantendo a configuração dependente do ambiente fora do código-fonte.
```

## O Que A IA Deve Fazer

- Explicar a responsabilidade técnica de cada módulo.
- Usar linguagem profissional e precisa.
- Preferir conceitos: persistência, autenticação, orquestração, domínio, integração, validação, observabilidade, pipelines, deploy.
- Evitar detalhes internos irrelevantes quando não ajudam a compreender arquitetura.
- Mostrar compromissos técnicos quando há decisão técnica.
- Indicar limitações reais com honestidade.
- Escrever documentação preparada para equipa técnica, recrutador, cliente ou maintainer futuro.

## O Que Evitar

- Frases vagas: "faz coisas", "trata cenas", "liga à DB", "manda dados".
- Buzzwords sem conteúdo.
- Promessas não validadas.
- Comentários óbvios.
- Explicações que dependem de nomes internos do utilizador.
- Linguagem demasiado informal em documentação.

## Modelo mental

Ao explicar um componente, responder:

```text
O que é?
Que responsabilidade tem?
Que problema resolve?
Com que componentes comunica?
Como é configurado?
Como é testado?
Como evolui sem quebrar o sistema?
```

## Checklist

```text
[ ] A explicação é conceptual.
[ ] A responsabilidade técnica está clara.
[ ] Não depende de nomes internos irrelevantes.
[ ] Não há buzzwords vazias.
[ ] A documentação parece profissional.
[ ] A solução está preparada para manutenção e escala.
```
