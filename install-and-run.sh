#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/chuckyLeeVIII/BTCRecover-Advance.git"
REPO_DIR="$HOME/BTCRecover-Level-Up"

echo "[*] BTCRecover-Level-Up installer starting..."

# 1) Install uv if missing
if ! command -v uv >/dev/null 2>&1; then
  echo "[*] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "[*] uv already installed."
fi

# 2) Clone or update repo
if [ -d "$REPO_DIR/.git" ]; then
  echo "[*] Updating existing repo at $REPO_DIR..."
  cd "$REPO_DIR"
  git pull --ff-only
else
  echo "[*] Cloning repo into $REPO_DIR..."
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi

# 3) Create venv and install deps
echo "[*] Creating virtualenv with uv..."
uv venv

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  # shellcheck disable=SC1091
  . .venv/Scripts/activate
fi

echo "[*] Installing dependencies with uv pip..."
uv pip install -r requirements.txt

echo "[*] Launching BTCRecover-Level-Up UI..."
python ui_launcher.py
