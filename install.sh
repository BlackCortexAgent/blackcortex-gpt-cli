#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.gpt-cli"
GLOBAL_BIN="$HOME/.local/bin/gpt"
SCRIPT_ENTRY="gpt.py"

echo "📦 Installing GPT CLI to $INSTALL_DIR"

# Prompt if already installed
if [ -d "$INSTALL_DIR" ]; then
  read -p "⚠️ GPT CLI already exists at $INSTALL_DIR. Overwrite? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ Install cancelled."
    exit 1
  fi
  rm -rf "$INSTALL_DIR"
fi

# Create install directory and copy gpt.py
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_ENTRY" "$INSTALL_DIR/"

# Create empty .env if not already present
touch "$INSTALL_DIR/.env"

# Create virtual environment
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install dependencies if available
if [ -f requirements.txt ]; then
  echo "📄 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
fi

# Ensure ~/.local/bin exists
mkdir -p "$(dirname "$GLOBAL_BIN")"

# Write launcher
cat <<EOF > "$GLOBAL_BIN"
#!/usr/bin/env bash
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"

# Load environment variables from .env
export \$(grep -v '^#' .env | xargs)

exec python $SCRIPT_ENTRY "\$@"
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

echo "✅ GPT CLI installed successfully! Run it with: gpt"
