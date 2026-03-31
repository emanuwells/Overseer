# AI Handoff Checklist (Overseer)

## Objetivo
Checklist mínima para qualquer IA integrar um novo pipeline sem quebrar o runtime.

## Ordem de leitura obrigatória
1. `README.md`
2. `docs/PRD_PM_Universal_DropIn_AI_Ready.md`
3. `pipelines/_template/pipeline.yaml`
4. `pipelines/_template/config/monitoring.json.example`
5. `orchestrator.py`
6. `overseer_monitor/monitor.py`

## Passos obrigatórios para adicionar pipeline
1. Criar `pipelines/<pipeline_id>/` a partir de `_template/`.
2. Definir `pipeline_id` e `entrypoint` no YAML.
3. Ajustar `runner_host`:
   - `auto` para runner local automático.
   - `any` para qualquer runner.
   - hostname fixo para pinning.
4. Implementar script(s) em `pipelines/<pipeline_id>/src/`.
5. Garantir uso de `OverseerMonitor` no fluxo do pipeline.
6. Executar:
   - `python orchestrator.py run <pipeline_id>`
   - `python scripts/export_payload_from_db.py`
7. Confirmar dados em:
   - `frontend/pm_payload.json`
   - `frontend/pm_details.json`

## Validação mínima
1. `python orchestrator.py list` mostra o pipeline.
2. Run cria registo em `logs`.
3. Frontend abre em `frontend/PM.html` e apresenta run.
4. Sem secrets reais commitados.

## Regras de segurança
1. Nunca escrever credenciais reais em ficheiros `.example`.
2. Nunca versionar `secrets/*.json` reais.
3. Nunca remover `.gitignore` de proteção de runtime/secrets.



