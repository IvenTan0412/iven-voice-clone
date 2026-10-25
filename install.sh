#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo "此套件需要原生运行的 M 系列 Mac（arm64）；不要在 Rosetta 终端中安装。" >&2
  exit 2
fi
macos_version="$(sw_vers -productVersion)"
if [[ "${macos_version%%.*}" -lt 14 ]]; then
  echo "此套件的 MLX 运行环境需要 macOS 14 或更新版本。" >&2
  exit 2
fi
runtime="${VOICE_CLONE_HOME:-$HOME/.local/share/iven-voice-clone}"
target="${VOICE_CLONE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/iven-voice-clone}"
mkdir -p "$runtime"
uv_bin="${VOICE_CLONE_UV:-$(command -v uv || true)}"
if [[ -z "$uv_bin" && -x "$HOME/.local/bin/uv" ]]; then uv_bin="$HOME/.local/bin/uv"; fi
if [[ -z "$uv_bin" && -x "$runtime/tools/uv" ]]; then uv_bin="$runtime/tools/uv"; fi
if [[ -z "$uv_bin" ]]; then
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  curl --fail --location --silent --show-error https://astral.sh/uv/0.11.16/install.sh -o "$installer"
  UV_INSTALL_DIR="$runtime/tools" UV_NO_MODIFY_PATH=1 sh "$installer"
  uv_bin="$runtime/tools/uv"
fi
"$uv_bin" python install 3.11.15
if [[ ! -x "$runtime/.venv/bin/python" ]]; then
  "$uv_bin" venv --python 3.11.15 "$runtime/.venv"
fi
"$uv_bin" pip sync --python "$runtime/.venv/bin/python" --require-hashes --only-binary :all: "$root/requirements.lock"
"$runtime/.venv/bin/python" "$root/scripts/setup.py" --runtime "$runtime" --skill-dir "$target"
