# Catálogos de runners

Este diretório contém apenas exemplos públicos. Catálogos reais incluem caminhos, hosts e comandos do ambiente e devem permanecer num diretório privado indicado por `OVERSEER_RUNNERS_DIR`.

## Estrutura privada

```text
<runners-dir>/
  hosts.yaml
  host-a.yaml
  host-b.yaml
```

Copie `_example.yaml` para o diretório privado, atribua-lhe o nome do `host_id` e ajuste os comandos. O ficheiro `hosts.yaml` segue o formato de `_hosts.example.yaml`.

O Compose de produção recusa arrancar sem `OVERSEER_RUNNERS_DIR`. Esta proteção evita publicar ou substituir acidentalmente configuração operacional.
