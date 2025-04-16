#!/usr/bin/env bash

set -eu  # Exit on error and treat unset vars as errors

INSTALL_DIR="$HOME/.gpt-cli"
GLOBAL_BIN="$HOME/.local/bin/gpt"
REQUIREMENTS="requirements.txt"

# --- Ensure venv is available ---
if ! python3 -m venv --help > /dev/null 2>&1; then
  echo "⚠️ Python venv not found. Attempting to install it..."
  sudo apt update && sudo apt install -y python3-venv
fi

# --- Detect if inside INSTALL_DIR ---
CURRENT_DIR="$(pwd)"
if [[ "$CURRENT_DIR" != "$INSTALL_DIR" ]]; then
  echo "📦 Installing GPT CLI to $INSTALL_DIR"

  mkdir -p "$INSTALL_DIR"

  # Remove the old .git
  rm -rf "$INSTALL_DIR/.git"

  # Copy all files including dotfiles
  shopt -s dotglob
  cp -r ./* "$INSTALL_DIR/"
  shopt -u dotglob

  echo "📁 Copied all project files (including dotfiles) to $INSTALL_DIR"
  cd "$INSTALL_DIR"
else
  echo "📦 Updating GPT CLI in $INSTALL_DIR"
  git pull || echo "⚠️ Not a git repo or pull failed, continuing..."
fi

# --- Create .env if missing ---
if [ ! -f "$INSTALL_DIR/.env" ]; then
  cat <<EOF > "$INSTALL_DIR/.env"
# GPT CLI Configuration
# Uncomment to override default values

#OPENAI_API_KEY=
#OPENAI_MODEL=
#OPENAI_DEFAULT_PROMPT=
#OPENAI_LOGFILE=
#OPENAI_TEMPERATURE=
#OPENAI_MAX_TOKENS=
#OPENAI_MAX_SUMMARY_TOKENS=
#OPENAI_MEMORY_PATH=
#OPENAI_MEMORY_LIMIT=
#OPENAI_STREAM_ENABLED=
EOF
  chmod 600 "$INSTALL_DIR/.env"
  echo "📝 Created .env template at $INSTALL_DIR/.env"
fi

# --- Setup virtual environment ---
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

if [ -f "$REQUIREMENTS" ]; then
  echo "📄 Installing dependencies..."
  pip install -r "$REQUIREMENTS"
fi

# --- Create launcher in ~/.local/bin ---
mkdir -p "$(dirname "$GLOBAL_BIN")"
cat <<'EOF' > "$GLOBAL_BIN"
#!/usr/bin/env bash
source "$HOME/.gpt-cli/venv/bin/activate"
cd "$HOME/.gpt-cli"
exec python gpt.py "$@"
EOF

chmod +x "$GLOBAL_BIN"

# --- Ensure ~/.local/bin is in PATH ---
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo "⚠️ ~/.local/bin is not in your PATH."

  read -p "👉 Add it to your shell config automatically? [y/N] " add_path
  if [[ "$add_path" =~ ^[Yy]$ ]]; then
    if [[ "$SHELL" == */zsh ]]; then
      SHELL_CONFIG="$HOME/.zshrc"
    elif [[ "$SHELL" == */bash ]]; then
      SHELL_CONFIG="$HOME/.bashrc"
    fi

    if [ -n "${SHELL_CONFIG:-}" ]; then
      if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_CONFIG"; then
        echo "🔧 Adding to $SHELL_CONFIG"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
        echo "✅ Done! Run: source $SHELL_CONFIG"
      else
        echo "ℹ️ ~/.local/bin is already configured in $SHELL_CONFIG"
      fi
    else
      echo "⚠️ Could not detect a supported shell config."
    fi
  fi
fi

echo ""
echo "✅ GPT CLI is ready!"
echo "🔐 Set API key: gpt --set-key"
echo "🛠️ Edit config: gpt --env"
echo "👉 Run: gpt"
