#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
PY="${VENV}/bin/python"

if [[ ! -x "${PY}" ]]; then
  echo "[ContentSuite] Creating virtual environment..."
  python3 -m venv "${VENV}"
fi

echo "[ContentSuite] Checking dependencies..."
"${PY}" -m pip install -r requirements.txt -q

CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/ContentSuite"
echo "[ContentSuite] Starting..."
echo "[ContentSuite] Config & log: ${CONFIG_DIR}/"

exec "${PY}" main.py