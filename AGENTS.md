# AGENTS.md - Overseer

## Read this first
1. `README.md`
2. `docs/PRD_PM_Universal_DropIn_AI_Ready.md`
3. `docs/AI_HANDOFF_CHECKLIST.md`
4. `CHANGELOG.md` (bloco da versao mais recente + `AI Context Delta`)

## Non-negotiable rules
- Keep runtime in no-API mode (`DB -> JSON -> frontend`).
- Keep folder structure homogeneous under `pipelines/<pipeline_id>/`.
- Never commit real secrets.
- Respect `runner_host` semantics:
  - `auto` or empty => local hostname
  - `any` => any runner
  - explicit hostname => pinned runner

## Mandatory verification after changes
- `python orchestrator.py list`
- `python scripts/export_payload_from_db.py`
- Frontend reads from `frontend/pm_payload.json` and `frontend/pm_details.json`

## Required docs update when behavior changes
- `README.md`
- `CHANGELOG.md`
- `docs/PRD_PM_Universal_DropIn_AI_Ready.md`

