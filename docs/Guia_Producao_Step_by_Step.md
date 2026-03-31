# Guia Step-by-Step: Colocar o Overseer em Produção

## 0. Objetivo
Este guia explica, sem ambiguidades, como pôr tudo a funcionar:
1. Orchestrator
2. overseer_monitor
3. Base de dados (`logs`)
4. Export DB -> JSON
5. Frontend no Nginx
6. Multi-máquina (runners diferentes)

## 1. Arquitetura final (desenho)
```text
                 +-----------------------+
                 |  Browser (User)      |
                 |  /apps/overseer/PM.html   |
                 +-----------+-----------+
                             |
                             | lê JSON estático
                             v
+----------------------+   +-------------------------------+
| Nginx                |   | /apps/overseer/pm_payload.json |
| serve /apps/overseer/* | | /apps/overseer/pm_details.json |
+----------------------+   +---------------+---------------+
                                            ^
                                            | gerado de 15 em 15 min
                                            |
                                  +---------+---------+
                                  | export_payload.py |
                                  +---------+---------+
                                            |
                                            | lê
                                            v
                                     +------+------+
                                     | MySQL/Maria |
                                     | logs + ...  |
                                     +------+------+
                                            ^
                                            | grava
               +----------------------------+----------------------------+
               |                                                         |
     +---------+---------+                                     +---------+---------+
     | Runner A          |                                     | Runner B          |
     | orchestrator.py   |                                     | orchestrator.py   |
     | pipeline X/Y      |                                     | pipeline Z        |
     +-------------------+                                     +-------------------+
```

## 2. Pré-requisitos
### 2.1 Servidor principal (Nginx + frontend)
- Ubuntu 22.04+
- Python 3.10+
- Nginx
- Acesso à DB MySQL/MariaDB

### 2.2 Em cada runner
- Python 3.10+
- Acesso de rede à mesma DB
- Código da pipeline local

## 3. Instalação no servidor principal
### 3.1 Copiar projeto
```bash
sudo mkdir -p /opt/overseer
sudo chown -R $USER:$USER /opt/overseer
cd /opt/overseer
```

### 3.2 Ambiente Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Credenciais
Criar:
- `secrets/database.json`
- `secrets/slack.json`

Exemplo `secrets/database.json`:
```json
{
  "database": {
    "host": "10.0.0.20",
    "port": 3306,
    "user": "monitor_user",
    "password": "SENHA_FORTE",
    "database": "monitor_db",
    "charset": "utf8mb4"
  }
}
```

## 4. Estrutura obrigatória de cada pipeline
```text
pipelines/<pipeline_id>/
  pipeline.yaml
  src/
    main.py
  config/
  secrets/
```

Exemplo `pipeline.yaml`:
```yaml
pipeline_id: faturacao_diaria
name: Faturacao Diaria
owner: data.team
criticality: high
runner_host: auto
schedule: "manual"
timeout_sec: 3600
retries: 2
entrypoint: "python src/main.py"
```

Regras `runner_host`:
- `auto`/vazio: hostname local
- `any`: qualquer runner
- `host-a`: runner fixo

## 5. Código mínimo com overseer_monitor
```python
from overseer_monitor import OverseerMonitor

monitor = OverseerMonitor.from_env("faturacao_diaria")
monitor.start()
try:
    with monitor.step("extract", context={"pipeline_id": "faturacao_diaria"}):
        pass
    with monitor.step("transform", parent_module_id="extract", context={"pipeline_id": "faturacao_diaria"}):
        pass
    monitor.finish(status="success", context={"pipeline_id": "faturacao_diaria"})
except Exception as exc:
    monitor.finish(status="failed", error_message=str(exc), context={"pipeline_id": "faturacao_diaria"})
    raise
```

## 6. Teste manual obrigatório
```bash
python orchestrator.py list
python orchestrator.py run faturacao_diaria
python scripts/export_payload_from_db.py
```

Validar:
- `frontend/pm_payload.json`
- `frontend/pm_details.json`

## 7. Publicar frontend no Nginx
Exemplo `/etc/nginx/sites-available/overseer`:
```nginx
server {
    listen 80;
    server_name monitor.seu-dominio.pt;

    root /usr/share/nginx/html/MAIATRON;

    location /apps/overseer/ {
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-store";
    }

    location /config/ {
        try_files $uri $uri/ =404;
    }
}
```

Ativar:
```bash
sudo ln -s /etc/nginx/sites-available/overseer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

URL:
- `http://monitor.seu-dominio.pt/apps/overseer/PM.html`

## 8. Cron de produção
```cron
*/15 * * * * cd /opt/overseer && .venv/bin/python scripts/export_payload_from_db.py >> runtime/logs/export.log 2>&1
10 2 * * * cd /opt/overseer && .venv/bin/python scripts/archive_logs.py --days 30 >> runtime/logs/archive.log 2>&1
* * * * * cd /opt/overseer && .venv/bin/python orchestrator.py trigger consume --runner $(hostname -s) --max 20 >> runtime/logs/trigger_consume.log 2>&1
* * * * * cd /opt/overseer && .venv/bin/python orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner $(hostname -s) --once --max 50 >> runtime/logs/trigger_consume_file.log 2>&1
```

## 9. Multi-máquina: operação
### Em cada runner
- Projeto disponível
- `secrets/database.json` configurado
- cron de `trigger consume` ativo

### Enfileirar execução
```bash
python orchestrator.py trigger enqueue faturacao_diaria --by Emanuel
python orchestrator.py trigger enqueue faturacao_diaria --by Emanuel --runner-host host-a
```

## 10. Checklist final
1. `orchestrator.py list` mostra pipelines
2. `logs` recebe runs novas
3. `/apps/overseer/pm_payload.json` atualiza
4. `/apps/overseer/PM.html` mostra dados
5. `archive_logs.py` move >30 dias para `logs_archive`

## 11. Troubleshooting rápido
### Frontend sem dados
- correr `python scripts/export_payload_from_db.py`
- validar ficheiros JSON em `/apps/overseer/` (ou symlink para `frontend/`)

### Pipeline não arranca
- validar `pipeline.yaml`
- testar `entrypoint` diretamente no shell
- confirmar `runner_host`

### Sem gravação na DB
- validar `secrets/database.json`
- validar conectividade à DB
- validar permissões do user da DB

## 12. O que enviar para outra IA
1. `docs/PRD_PM_Universal_DropIn_AI_Ready.md`
2. `docs/AI_HANDOFF_CHECKLIST.md`
3. `AGENTS.md`
4. `README.md`
5. `pipelines/_template/`




