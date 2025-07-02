#!/bin/bash
set -e

REPO_URL="https://github.com/saikat-here/logwatcher.git"
CLONE_DIR="/tmp/logwatcher"
INSTALL_DIR="/opt/LogWatcher"
SERVICE_NAME="logwatcher"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Detect Python 3 binary
PYTHON_BIN=$(command -v python3 || true)
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python3 is not installed. Please install Python 3 to continue."
    exit 1
fi

function uninstall() {
    echo "🛑 Stopping and disabling $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true

    echo "🧹 Cleaning up installation..."
    sudo rm -rf "$INSTALL_DIR"
    sudo rm -f "$SERVICE_FILE"

    echo "🔄 Reloading systemd..."
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload

    echo "✅ LogWatcher uninstalled."
    exit 0
}

# Handle uninstall option
if [[ "$1" == "--uninstall" ]]; then
    uninstall
fi

echo "🔽 Cloning the repository..."
rm -rf "$CLONE_DIR"
git clone "$REPO_URL" "$CLONE_DIR"

echo "📁 Installing to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"

echo "📄 Copying files to $INSTALL_DIR"
for file in "$CLONE_DIR/logwatcher/"*; do
    filename=$(basename "$file")
    if [[ "$filename" == "config.txt" && -f "$INSTALL_DIR/config.txt" ]]; then
        echo "⚠️  Skipping existing config.txt (preserved)"
        continue
    fi
    sudo cp "$file" "$INSTALL_DIR/"
done

sudo chmod +x "$INSTALL_DIR/LogWatcher.py"

echo "🔧 Updating systemd service file..."
# Replace hardcoded python3 path with actual detected path
sudo sed -i "s|^ExecStart=.*|ExecStart=$PYTHON_BIN $INSTALL_DIR/LogWatcher.py|" "$INSTALL_DIR/logwatcher.service"

echo "🔗 Installing service..."
sudo cp "$INSTALL_DIR/logwatcher.service" "$SERVICE_FILE"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "🔄 Restarting logwatcher service to apply changes..."
sudo systemctl restart logwatcher
echo "✅ LogWatcher service restarted successfully."

echo "✅ LogWatcher installed and running with $PYTHON_BIN"

