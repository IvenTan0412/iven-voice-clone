#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime="${VOICE_CLONE_HOME:-}"
if [[ -z "$runtime" && -f "$root/.runtime-path" ]]; then
  IFS= read -r runtime < "$root/.runtime-path"
fi
runtime="${runtime:-$HOME/.local/share/iven-voice-clone}"
if [[ ! -x "$runtime/.venv/bin/python" ]]; then
  echo "缺少运行环境，请先执行：bash \"$root/install.sh\"" >&2
  exit 2
fi
export VOICE_CLONE_HOME="$runtime"
exec "$runtime/.venv/bin/python" "$root/scripts/voice.py" "$@"
