#!/bin/bash
set -e

SERVICE_NAME="logwatcher"
INSTALL_DIR="/opt/LogWatcher"
SERVICE_FILE="/etc/systemd/system/logwatcher.service"

echo "🛑 Stopping service..."
sudo systemctl stop "$SERVICE_NAME" || true
sudo systemctl disable "$SERVICE_NAME" || true

echo "🧹 Cleaning up files..."
sudo rm -rf "$INSTALL_DIR"
sudo rm -f "$SERVICE_FILE"

echo "🔄 Reloading systemd"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "✅ LogWatcher uninstalled."
