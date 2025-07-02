#!/bin/bash
set -e

SERVICE_NAME="logwatcher"
INSTALL_DIR="/opt/LogWatcher"
SERVICE_FILE="logwatcher.service"

echo "📁 Installing to $INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"
sudo cp LogWatcher.py config.txt logwatcher.service install_logwatcher.sh uninstall_logwatcher.sh "$INSTALL_DIR"
sudo chmod +x "$INSTALL_DIR/LogWatcher.py"

echo "🔗 Setting up systemd service"
sudo cp "$INSTALL_DIR/$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "✅ LogWatcher installed and running."
