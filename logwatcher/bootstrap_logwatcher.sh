#!/bin/bash
set -e

REPO_URL="https://github.com/saikat-here/logwatcher.git"
CLONE_DIR="/tmp/logwatcher"
INSTALL_DIR="/opt/LogWatcher"
SERVICE_NAME="logwatcher"
SERVICE_FILE="logwatcher.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_FILE"

# Detect Python 3
PYTHON_BIN=$(command -v python3)
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python 3 is required but not found. Exiting."
    exit 1
fi

function uninstall() {
    echo "🛑 Stopping $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true
    echo "🧹 Removing files..."
    sudo rm -rf "$INSTALL_DIR"
    sudo rm -f "$SYSTEMD_PATH"
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    echo "✅ Uninstalled LogWatcher."
    exit 0
}

if [[ "$1" == "--uninstall" ]]; then
    uninstall
fi

echo "🔽 Cloning repository..."
rm -rf "$CLONE_DIR"
git clone "$REPO_URL" "$CLONE_DIR"

echo "📁 Creating install directory..."
sudo mkdir -p "$INSTALL_DIR/log"

echo "Stoping service to apply updates..."
sudo systemctl stop "$SERVICE_NAME"

echo "📄 Copying files (preserving config.txt if present)..."
for file in "$CLONE_DIR/logwatcher/"*; do
    filename=$(basename "$file")
    
    if [[ "$filename" == "config.txt" && -f "$INSTALL_DIR/config.txt" ]]; then
        echo "⚠️  Skipping existing config.txt"
        continue
    fi

    if [ -d "$file" ]; then
        echo "📂 Copying directory: $filename"
        sudo cp -rf "$file" "$INSTALL_DIR/"
    else
        sudo cp -f "$file" "$INSTALL_DIR/"
    fi
done


echo "📂 Creating pattern directory..."
sudo mkdir -p "$INSTALL_DIR/pattern"

# custompattern: create only if missing
if [ ! -f "$INSTALL_DIR/pattern/custompattern.txt" ]; then
    sudo touch "$INSTALL_DIR/pattern/custompattern.txt"
    echo "✅ custompattern created"
else
    echo "⚠️  custompattern already exists, preserving that"
fi

echo "📄 Creating empty excluded_lines.txt if not present..."
EXCLUDE_FILE="$INSTALL_DIR/pattern/excluded_lines.txt"

if [ ! -f "$EXCLUDE_FILE" ]; then
    sudo touch "$EXCLUDE_FILE"
    echo "✅ excluded_lines.txt created in pattern/"
else
    echo "⚠️ excluded_lines.txt already exists in pattern/, skipping"
fi


echo "🔧 Making LogWatcher.py executable..."
sudo chmod +x "$INSTALL_DIR/LogWatcher.py"

echo "🔧 Updating ExecStart with detected Python path..."
sudo sed -i "s|^ExecStart=.*|ExecStart=$PYTHON_BIN $INSTALL_DIR/LogWatcher.py|" "$INSTALL_DIR/$SERVICE_FILE"

echo "🔗 Installing service..."
sudo cp "$INSTALL_DIR/$SERVICE_FILE" "$SYSTEMD_PATH"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "🔄 Restarting service to apply updates..."
sudo systemctl restart "$SERVICE_NAME"

echo "✅ LogWatcher is up and running."



echo ""
echo "🎉 Installation Complete!"
echo "---------------------------------------------"
echo "📂 LogWatcher files installed to: $INSTALL_DIR"
echo ""
echo "📄 Key Files:"
echo "  • Main Script       : $INSTALL_DIR/LogWatcher.py"
echo "  • Config File       : $INSTALL_DIR/config.txt"
echo "  • Pattern Folder    : $INSTALL_DIR/pattern/"
echo "      ├─ defaultpattern"
echo "      ├─ custompattern"
echo "      └─ excluded_lines.txt"
echo "  • Logs Folder       : $INSTALL_DIR/log/"
echo "      ├─ LogWatcher.log     (operational log)"
echo "      └─ matches.log        (pattern match log)"
echo ""
echo "⚙️  Service: logwatcher"
echo "  • Start   : sudo systemctl start logwatcher"
echo "  • Stop    : sudo systemctl stop logwatcher"
echo "  • Status  : sudo systemctl status logwatcher"
echo "  • Logs    : journalctl -u logwatcher -n 50 --no-pager"
echo ""
echo "📝 To customize:"
echo "  • Scan interval   : edit 'scan_interval' in config.txt"
echo "  • Patterns        : edit 'pattern/defaultpattern' or 'custompattern'"
echo "  • Exclusions      : add lines to 'pattern/excluded_lines.txt'"
echo ""
echo "🔁 Changes take effect automatically on next scan (every N seconds)."
echo "---------------------------------------------"

