#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Uso: bash scripts/deploy-production-api.sh [--dry-run]

Publica apenas os ficheiros declarados em api/catalog.json para a raiz plana
da API. O script não faz git pull e não remove ficheiros de outros repos.
EOF
}

dry_run=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; usage >&2; exit 2 ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="${repo_root}/api/catalog.json"
api_root="${API_ROOT:-/usr/share/nginx/html/api}"
backup_root="${API_BACKUP_ROOT:-/home/eferreira/Dev/backups/api-deploy}"
public_base_url="${API_PUBLIC_BASE_URL:-http://127.0.0.1}"

command -v git >/dev/null || { echo 'git não está disponível.' >&2; exit 1; }
command -v php >/dev/null || { echo 'php não está disponível.' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'python3 não está disponível.' >&2; exit 1; }
command -v curl >/dev/null || { echo 'curl não está disponível.' >&2; exit 1; }
command -v flock >/dev/null || { echo 'flock não está disponível.' >&2; exit 1; }
[[ -f "$manifest" ]] || { echo "Manifesto em falta: $manifest" >&2; exit 1; }

php_version="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')"
[[ "$php_version" == '7.4' ]] || {
  echo "O deploy exige PHP 7.4 para lint; encontrado ${php_version}." >&2
  exit 1
}

mapfile -t metadata < <(python3 - "$manifest" <<'PY'
import json, pathlib, re, sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
owner = data.get("owner", "")
if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner):
    raise SystemExit("owner inválido no manifesto")
print(f"OWNER\t{owner}")
for item in data.get("files", []):
    source = item.get("source", "")
    target = item.get("target", "")
    route = item.get("route", "")
    if not source.startswith("api/") or pathlib.PurePosixPath(source).is_absolute():
        raise SystemExit(f"source inválido: {source}")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.php", target):
        raise SystemExit(f"target inválido: {target}")
    print(f"FILE\t{source}\t{target}\t{route}")
PY
)

owner="${metadata[0]#OWNER$'\t'}"
declare -a sources=() targets=() routes=()
for line in "${metadata[@]:1}"; do
  IFS=$'\t' read -r kind source target route <<<"$line"
  [[ "$kind" == FILE ]] || continue
  sources+=("$source")
  targets+=("$target")
  routes+=("${route:-}")
done
[[ ${#sources[@]} -gt 0 ]] || { echo 'Manifesto sem ficheiros.' >&2; exit 1; }

cd "$repo_root"
[[ "$(git branch --show-current)" == main ]] || { echo 'O deploy exige a branch main.' >&2; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo 'O repo tem alterações locais; deploy recusado.' >&2; exit 1; }
origin_url="$(git remote get-url origin)"
remote_head="$(git ls-remote "$origin_url" refs/heads/main | awk '{print $1}')"
local_head="$(git rev-parse HEAD)"
[[ -n "$remote_head" && "$local_head" == "$remote_head" ]] || {
  echo 'HEAD local não coincide com origin/main; deploy recusado.' >&2
  exit 1
}

for source in "${sources[@]}"; do
  [[ -f "$source" ]] || { echo "Ficheiro em falta: $source" >&2; exit 1; }
  php -l "$source" >/dev/null
done

echo "Repo: $owner"
echo "Commit: $local_head"
echo "Destino: $api_root"
printf 'Payload: %s\n' "${targets[*]}"
if [[ $dry_run -eq 1 ]]; then
  echo 'Dry-run concluído; produção não foi alterada.'
  exit 0
fi

mkdir -p "$api_root" "$backup_root/$owner"
exec 9>/tmp/cm-maia-api-deploy.lock
flock -x 9

timestamp="$(date +%Y%m%d_%H%M%S)"
backup_dir="$backup_root/$owner/$timestamp"
stage_dir="$(mktemp -d "${api_root}/.${owner}.stage.XXXXXX")"
mkdir -p "$backup_dir"

rollback() {
  set +e
  echo 'Falha detetada; a restaurar o payload anterior.' >&2
  for target in "${targets[@]}"; do
    if [[ -f "$backup_dir/$target" ]]; then
      install -m 0644 "$backup_dir/$target" "$api_root/$target"
    elif [[ -f "$backup_dir/.missing-$target" ]]; then
      rm -f -- "$api_root/$target"
    fi
  done
}
cleanup() { rm -rf -- "$stage_dir"; }
trap cleanup EXIT
trap 'rollback' ERR

for index in "${!sources[@]}"; do
  source="${sources[$index]}"
  target="${targets[$index]}"
  if [[ -f "$api_root/$target" ]]; then
    cp -p -- "$api_root/$target" "$backup_dir/$target"
  else
    : >"$backup_dir/.missing-$target"
  fi
  install -m 0644 "$source" "$stage_dir/$target"
  php -l "$stage_dir/$target" >/dev/null
done

for target in "${targets[@]}"; do
  pending="$api_root/.${target}.new.${timestamp}"
  install -m 0644 "$stage_dir/$target" "$pending"
  mv -f -- "$pending" "$api_root/$target"
done

for route in "${routes[@]}"; do
  [[ -n "$route" ]] || continue
  curl -fsS --max-time 30 "${public_base_url}${route}" >/dev/null
done

trap - ERR
echo "Deploy concluído. Backup: $backup_dir"
