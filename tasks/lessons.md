# Aprendizagens

## Digests informativos não devem funcionar como alarmes

Um resumo periódico deve separar informação operacional de sinais acionáveis. Heartbeats e filas continuam disponíveis para diagnóstico na API e na interface, mas não precisam de ocupar o digest. Menções globais devem ficar reservadas a falhas abertas ou quebras de cadência, evitando alarmes em ciclos normais de manutenção e deploy.

## Configuração operacional fora do checkout

Catálogos de runners podem conter infraestrutura identificável e comandos privados. Devem residir num diretório externo selecionado por `OVERSEER_RUNNERS_DIR`, com apenas exemplos genéricos no Git.

O runtime persistente deve ser selecionado por `OVERSEER_RUNTIME_DIR` para não ficar acoplado ao ciclo de vida do checkout.

## Reescrita de história exige rollback independente

Antes de substituir a história Git, criar e verificar um bundle completo fora do repositório. Produção deve conservar configuração, runtime, SHA e imagem anteriores até a nova revisão passar health checks.
