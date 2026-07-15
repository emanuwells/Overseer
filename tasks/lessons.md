# Aprendizagens

## Digests informativos não devem funcionar como alarmes

Um resumo periódico deve separar informação operacional de sinais acionáveis. Heartbeats e filas continuam disponíveis para diagnóstico na API e na interface, mas não precisam de ocupar o digest. Menções globais devem ficar reservadas a falhas abertas ou quebras de cadência, evitando alarmes em ciclos normais de manutenção e deploy.

## Configuração operacional fora do checkout

Catálogos de runners podem conter infraestrutura identificável e comandos privados. Devem residir num diretório externo selecionado por `OVERSEER_RUNNERS_DIR`, com apenas exemplos genéricos no Git.

O runtime persistente deve ser selecionado por `OVERSEER_RUNTIME_DIR` para não ficar acoplado ao ciclo de vida do checkout.

## Reescrita de história exige rollback independente

Antes de substituir a história Git, criar e verificar um bundle completo fora do repositório. Produção deve conservar configuração, runtime, SHA e imagem anteriores até a nova revisão passar health checks.

Para remover `Co-authored-by: Cursor` sem alterar árvores de ficheiros, usar `git filter-repo` com callback de mensagem (`scripts/run_strip_coauthor_filter.py` como referência one-shot). O `git filter-repo` remove o remote `origin`; readicionar antes do push. Após force push, todos os clones precisam de `git fetch` + `reset --hard origin/main`.

## Slack em produção depende de `secrets/slack.json`

O digest agendado (08:30 Europe/Lisbon) e os alertas imediatos só enviam quando `get_slack_notifier().is_enabled` é verdadeiro. Em baze2, a ausência de `secrets/slack.json` (ou `OVERSEER_SLACK_WEBHOOK_URL` válido) deixava `webhook_configured=False` sem erro visível na UI. Validar com diagnóstico read-only no contentor antes de assumir falha de cron.

## Frontend Node em repositórios no Google Drive

`npm install` directamente em `frontend/node_modules` num checkout sincronizado com Google Drive falha com EPERM/EBADF. Gerar `package-lock.json` e validar `npm run build` num diretório temporário local (ou no stage Docker). O build de produção deve depender do Dockerfile, não de `node_modules` versionado.

## `.gitignore` com padrões amplos

A regra `templates/` na raiz ignorava também `docs/resources/templates/`, impedindo versionar `.env.example`. Preferir âncoras à raiz (`/templates/`) quando o padrão for legado local, não documentação versionada.
