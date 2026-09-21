#!/usr/bin/env bash
# SessionStart hook: kích hoạt conda env của project cho mọi lệnh Bash của
# Claude Code, bằng cách ghi biến môi trường vào $CLAUDE_ENV_FILE.
#
# Tương đương `conda activate action-recognition` trên Windows: đưa thư mục
# env, Library/bin (DLL của numpy/opencv/torch) và Scripts lên đầu PATH.
#
# Đổi tên env: đặt CONDA_ENV_NAME. Miniconda ở chỗ khác: đặt CONDA_ROOT.

ENV_NAME="${CONDA_ENV_NAME:-action-recognition}"
ROOT="${CONDA_ROOT:-$HOME/miniconda3}"
PREFIX="$ROOT/envs/$ENV_NAME"

if [ ! -x "$PREFIX/python.exe" ]; then
  echo "{\"systemMessage\": \"Không tìm thấy conda env '$ENV_NAME' tại $PREFIX — lệnh python sẽ dùng Python hệ thống.\"}"
  exit 0
fi

[ -n "$CLAUDE_ENV_FILE" ] || exit 0

cat >> "$CLAUDE_ENV_FILE" <<ENVEOF
export CONDA_PREFIX="$PREFIX"
export CONDA_DEFAULT_ENV="$ENV_NAME"
export PATH="$PREFIX:$PREFIX/Library/mingw-w64/bin:$PREFIX/Library/usr/bin:$PREFIX/Library/bin:$PREFIX/Scripts:$PREFIX/bin:\$PATH"
ENVEOF
