#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-10.45.0.4}"
REMOTE_USER="${REMOTE_USER:-codex}"
SSH_KEY="${SSH_KEY:-/lab/projects/livecopilot/lab/vms/livecopilot-validation/admin_sshkey}"
INSTALL="${INSTALL:-0}"

usage() {
  cat <<'EOF'
Uso:
  scripts/bootstrap_layer0_vm.sh [--install]

Variáveis:
  REMOTE_HOST  host remoto (padrão: 10.45.0.4)
  REMOTE_USER  usuário SSH (padrão: codex)
  SSH_KEY      chave SSH (padrão canônico da VM)
  INSTALL=1 instala dependências mínimas via apt quando faltarem
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install)
      INSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "argumento desconhecido: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" \
  "INSTALL='$INSTALL' bash -s" <<'REMOTE'
set -euo pipefail

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

has_python_psycopg() {
  python3 - <<'PY' >/dev/null 2>&1
import psycopg
PY
}

missing=()

for cmd in python3 traceroute curl; do
  if ! need_cmd "$cmd"; then
    missing+=("$cmd")
  fi
done

if ! need_cmd dig && ! need_cmd host && ! need_cmd getent; then
  missing+=("dns-tool")
fi

if ! has_python_psycopg; then
  missing+=("python3-psycopg")
fi

if (( ${#missing[@]} > 0 )); then
  printf '%s\n' "faltando: ${missing[*]}" >&2
  if [[ "${INSTALL}" == "1" ]]; then
    sudo apt-get update
    sudo apt-get install -y python3-psycopg dnsutils traceroute curl
  else
    exit 1
  fi
fi

printf 'hostname=%s\n' "$(hostname)"
printf 'whoami=%s\n' "$(whoami)"
printf 'pwd=%s\n' "$(pwd)"
printf 'python3=%s\n' "$(command -v python3)"
printf 'traceroute=%s\n' "$(command -v traceroute)"
printf 'curl=%s\n' "$(command -v curl)"
printf 'dns_tool=%s\n' "$(command -v dig || command -v host || command -v getent)"
python3 - <<'PY'
import psycopg
print(f"psycopg={psycopg.__version__}")
PY
REMOTE
