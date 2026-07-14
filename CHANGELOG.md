# Changelog

As alterações relevantes ao Overseer são registadas neste ficheiro.

## [5.8.26] - 2026-07-14

### Changed

- Preparado o repositório para consulta pública sob licença proprietária.
- Externalizada a configuração real de runners através de `OVERSEER_RUNNERS_DIR`.
- Externalizado o estado de runtime através de `OVERSEER_RUNTIME_DIR`.
- Substituída documentação específica de ambientes privados por instruções agnósticas.
- Simplificada a governação do repositório e removidos templates e adaptadores redundantes.

### Security

- Removidos da árvore pública hosts, endereços, utilizadores, caminhos e catálogos operacionais reais.
