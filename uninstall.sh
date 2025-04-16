#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.gpt-cli"
GLOBAL_BIN="$HOME/.local/bin/gpt"

echo "📦 Uninstalling GPT CLI..."

# Confirm with user
read -p "⚠️ Are you sure you want to uninstall GPT CLI? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "❌ Uninstall cancelled."
  exit 0
fi

# Remove launcher
if [ -f "$GLOBAL_BIN" ]; then
  echo "✅ Removing launcher from $GLOBAL_BIN"
  rm -f "$GLOBAL_BIN"
else
  echo "ℹ️ Launcher not found at $GLOBAL_BIN"
fi

# Remove install directory
if [ -d "$INSTALL_DIR" ]; then
  echo "✅ Deleting install directory at $INSTALL_DIR"
  rm -rf "$INSTALL_DIR"
else
  echo "ℹ️ Install directory not found at $INSTALL_DIR"
fi

echo "✅ GPT CLI has been uninstalled."
