#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-10.45.0.4}"
REMOTE_USER="${REMOTE_USER:-codex}"
SSH_KEY="${SSH_KEY:-/lab/projects/livecopilot/lab/vms/livecopilot-validation/admin_sshkey}"
REMOTE_ROOT="${REMOTE_ROOT:-/tmp/topomemory-runner}"
TARGET="${1:-example.com}"
SCENARIO="${2:-home_page}"
DATABASE_URL="${DATABASE_URL:-}"

usage() {
  cat <<'EOF'
Uso:
  scripts/run_layer0_remote.sh [target] [scenario]

Variáveis:
  DATABASE_URL  DSN oficial do banco topomemory, usado pelo runner remoto
  REMOTE_HOST   host da VM oficial (padrão: 10.45.0.4)
  REMOTE_USER   usuário SSH (padrão: codex)
  SSH_KEY       chave SSH canônica
EOF
}

if [[ "${TARGET}" == "-h" || "${TARGET}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -z "$DATABASE_URL" ]]; then
  echo "ERRO: DATABASE_URL não definido" >&2
  exit 2
fi

ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "rm -rf '$REMOTE_ROOT' && mkdir -p '$REMOTE_ROOT/src' '$REMOTE_ROOT/runs' '$REMOTE_ROOT/schemas'"

tar -C "$REPO_ROOT" -cf - src/collect_minimal_run.py src/ingest_run_bundle.py | \
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "tar -C '$REMOTE_ROOT' -xf -"

"$REPO_ROOT/scripts/bootstrap_layer0_vm.sh" --install

ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" \
  "cd '$REMOTE_ROOT' && DATABASE_URL='$DATABASE_URL' python3 src/collect_minimal_run.py '$TARGET' --scenario '$SCENARIO' --database-url '$DATABASE_URL'"
