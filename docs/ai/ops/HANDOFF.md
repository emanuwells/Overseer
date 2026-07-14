# Handoff — preparação para publicação pública

## Estado

- Configuração real de runners externalizada por `OVERSEER_RUNNERS_DIR`.
- Catálogos privados preservados fora da árvore rastreada.
- Documentação, testes e exemplos anonimizados.
- História anterior preservada num bundle privado verificado.
- Produção preservada num snapshot privado com configuração, runtime, SHA e imagem.
- História limpa publicada com um único commit e confirmada através de clone novo.
- Produção migrada; API, base de dados e dashboard validados.
- Alteração da visibilidade GitHub pendente porque o ambiente não dispõe de `gh` e o navegador autenticado não inicializou.

## Validação

- Testes Python: 98 passaram.
- Compose de desenvolvimento e produção: configuração válida com variáveis explícitas.
- Build Docker: concluído.
- Python, JavaScript e PowerShell: sintaxe válida.
- Links Markdown locais: válidos.
- Bash: não validado localmente porque WSL/bash não está instalado no ambiente Windows.

## Rollback

Restaurar o checkout, `.env`, catálogos, runtime e imagem registados no snapshot pré-migração. Não remover volumes.
