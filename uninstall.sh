#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.gpt-cli"
SCRIPT_NAME="gpt"
GLOBAL_BIN="$HOME/.local/bin/$SCRIPT_NAME"

echo "🧼 Uninstalling GPT CLI..."

# Confirm with user before uninstalling
read -p "⚠️ Are you sure you want to uninstall GPT CLI? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "❌ Uninstall cancelled."
  exit 0
fi

# Step 1: Remove global binary
if [ -f "$GLOBAL_BIN" ]; then
  echo "🔧 Removing launcher from $GLOBAL_BIN"
  rm -f "$GLOBAL_BIN"
else
  echo "ℹ️ Launcher not found at $GLOBAL_BIN"
fi

# Step 2: Remove installed directory
if [ -d "$INSTALL_DIR" ]; then
  echo "🗑 Deleting installation directory at $INSTALL_DIR"
  rm -rf "$INSTALL_DIR"
else
  echo "ℹ️ Install directory not found at $INSTALL_DIR"
fi

echo "✅ GPT CLI has been fully uninstalled."
