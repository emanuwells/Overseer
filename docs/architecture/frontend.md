# Arquitetura Frontend

## Responsabilidade

O frontend do Overseer é uma UI estática read-only para observar estado operacional. A interface não é a fonte de verdade para alterações de catálogo, execução ou sync remoto; essas operações são feitas por API, CLI ou scripts operacionais.

## Estrutura

| Área | Ficheiros | Responsabilidade |
|---|---|---|
| Páginas | `frontend/*.html` | Entrypoints estáticos para dashboard, deployments, lineage e detalhe de runs |
| Lógica cliente | `frontend/js/app.js` | Chamadas à API, renderização de estados e navegação |
| Configuração cliente | `frontend/js/overseer-config.example.js` | Exemplo seguro para URL/token local |
| Estilos | `frontend/css/app.css` | Layout, componentes visuais e responsividade |

## Integração API

- A UI consome principalmente endpoints `/v1/read/*`.
- Tokens devem ser configurados fora do Git quando necessários.
- A UI não deve expor segredos reais nem incorporar credenciais versionadas.
- Erros de API devem ser apresentados como estados de leitura, sem alterar dados.

## Rotas E Entrega

- A API serve o frontend em `/ui/`.
- `/` e `/ui` redirecionam para `/ui/dashboard.html`.
- O Dockerfile não tem build Node/Vite porque o frontend é estático.

## Regras De Evolução

- Preservar o caráter read-only salvo decisão arquitetural explícita.
- Não adicionar dependências frontend sem justificar benefício e custo operacional.
- Validar alterações com browser ou teste manual quando houver impacto visual ou de integração.
- Manter textos em português europeu quando forem documentação ou conteúdo controlado pelo projeto.
