# Language Policy

## Idioma Principal

- **Documentação**: Português europeu com acentuação correta
- **Código**: Inglês técnico (identificadores, comentários, docstrings)
- **Exceções**: Nomes técnicos, comandos, identificadores em inglês

## Regras de Documentação

### Português Europeu

- Usar português europeu padrão
- Acentuação correta (á, é, í, ó, ú, â, ê, ô, ã, õ)
- Pontuação europeia (vírgula decimal, ponto de milhar)
- Termos técnicos em português quando existir tradução aceite

### Termos Técnicos em Inglês

Manter em inglês quando:

- É identificador de código ou API
- É comando ou flag de terminal
- É nome de ficheiro ou diretório
- É termo técnico sem tradução aceite
- É nome de variável ou função

### Exemplos

| Correto | Incorreto |
|---|---|
| configuração | config (em documentação) |
| `config.py` | `configuracao.py` |
| `POST /api/runs` | `POST /api/executa` |
| pipeline | oleoduto |
| webhook | gancho web |

## Regras de Código

### Comentários

- Docstrings em inglês técnico
- Comentários inline em português ou inglês conforme contexto
- Evitar comentários que apenas repetem o código

### Naming

- Funções e variáveis: snake_case em inglês
- Classes: PascalCase em inglês
- Constantes: UPPER_SNAKE_CASE em inglês
- Ficheiros: snake_case em inglês

## Validação

Verificar ortografia e acentuação antes de commit em documentação.