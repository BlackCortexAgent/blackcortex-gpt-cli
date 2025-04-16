#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.gpt-cli"
GLOBAL_BIN="$HOME/.local/bin/gpt"
SCRIPT_ENTRY="gpt.py"

echo "📦 Installing GPT CLI to $INSTALL_DIR"

# Update if already present
if [ -d "$INSTALL_DIR" ]; then
  echo "📁 Updating existing GPT CLI at $INSTALL_DIR"
else
  echo "📁 Creating GPT CLI directory at $INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
fi

# Create install directory and copy gpt.py
cp "$SCRIPT_ENTRY" "$INSTALL_DIR/"
cp "requirements.txt" "$INSTALL_DIR/"
cp "uninstall.sh" "$INSTALL_DIR/"

# Create .env template if not already present
if [ ! -f "$INSTALL_DIR/.env" ]; then
  cat <<EOF > "$INSTALL_DIR/.env"
# GPT CLI Configuration
# See: https://github.com/Konijima/gpt-cli
# Uncomment the lines you want to override.

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

# Create virtual environment
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip #--quiet

# Install dependencies if available
if [ -f requirements.txt ]; then
  echo "📄 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt #--quiet
fi

# Ensure ~/.local/bin exists
mkdir -p "$(dirname "$GLOBAL_BIN")"

# Write launcher
cat <<'EOF' > "$GLOBAL_BIN"
#!/usr/bin/env bash
source "$HOME/.gpt-cli/venv/bin/activate"
cd "$HOME/.gpt-cli"

# Load .env variables manually (line-by-line, skipping comments)
if [ -f .env ]; then
  while IFS='=' read -r key value; do
    # Ignore lines that are empty or start with #
    [[ -z "$key" || "$key" =~ ^# ]] && continue
    export "$key"="$value"
  done < .env
fi

exec python gpt.py "$@"
EOF

chmod +x "$GLOBAL_BIN"

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo "⚠️ ~/.local/bin is not in your PATH."

  read -p "👉 Do you want to add it to your shell config automatically? [y/N] " add_path
  if [[ "$add_path" =~ ^[Yy]$ ]]; then
    SHELL_CONFIG=""
    if [[ "$SHELL" == */zsh ]]; then
      SHELL_CONFIG="$HOME/.zshrc"
    elif [[ "$SHELL" == */bash ]]; then
      SHELL_CONFIG="$HOME/.bashrc"
    fi

    if [ -n "$SHELL_CONFIG" ]; then
      if ! grep -q 'export PATH="\$HOME/.local/bin:\$PATH"' "$SHELL_CONFIG"; then
        echo "🔧 Adding to $SHELL_CONFIG"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
        echo "✅ Done! Please run: source $SHELL_CONFIG"
      else
        echo "ℹ️ ~/.local/bin is already configured in $SHELL_CONFIG"
      fi
    else
      echo "⚠️ Could not detect a supported shell (bash or zsh)."
      echo "Please add this line manually to your shell config:"
      echo '   export PATH="$HOME/.local/bin:$PATH"'
    fi
  else
    echo "📎 To use 'gpt' globally, add this to your shell config manually:"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
  fi

  echo ""
fi

echo "✅ GPT CLI installed successfully!"
echo ""
echo "👉 To start using it, run:  gpt"
echo "🔐 To set your OpenAI API key:  gpt --set-key YOUR_API_KEY"
echo "🛠️  To edit configuration manually:  gpt --env"
