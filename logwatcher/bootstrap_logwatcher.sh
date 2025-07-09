#!/bin/bash
set -e

REPO_URL="https://github.com/saikat-here/logwatcher.git"
CLONE_DIR="/tmp/logwatcher"
INSTALL_DIR="/opt/LogWatcher"
SERVICE_NAME="logwatcher"
SERVICE_FILE="logwatcher.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_FILE"


# echo "Installing and configuring Python3.10 and related packages"
# sudo yum groupinstall "Development Tools" -y
#sudo yum install gcc openssl-devel bzip2-devel libffi-devel wget make -y
# cd /usr/src
# sudo wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
# sudo tar xzf Python-3.10.14.tgz
# cd Python-3.10.14
# sudo ./configure --enable-optimizations
# sudo make altinstall
# sudo /usr/local/bin/python3.10 -m ensurepip
# sudo /usr/local/bin/python3.10 -m pip install --upgrade pip
# sudo /usr/local/bin/python3.10 -m pip install transformers torch scikit-learn

echo "Deleting the existing model directory"
rm -rf "INSTALL_DIR/model"

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

echo "📁 Creating CVS file directory..."
sudo mkdir -p "$INSTALL_DIR/CSV"

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


echo "Downloading the model"
/usr/local/bin/python3.10 /opt/LogWatcher/model/model_download.py

echo "🔧 Making LogWatcher.py executable..."
sudo chmod +x "$INSTALL_DIR/LogWatcher.py"


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
echo "=========================================================="
echo "📂 LogWatcher Directory Structure and Purpose:"
echo ""
echo "📁 $INSTALL_DIR               → Main installation directory"
echo ""
echo "├── LogWatcher.py            → Main Python service script (daemon)"
echo "├── config.txt               → Main config file"
echo "│                              - Includes: directory to scan, scan interval, email list"
echo ""
echo "📁 pattern/                  → Contains all pattern definitions and exclusions"
echo "│   ├── defaultpattern         - Built-in regex patterns for secret/leak detection ( avoid editing this )"
echo "│   ├── custompattern          - User-defined custom regex patterns"
echo "│   └── excluded_lines.txt     - Substrings to suppress false-positive matches"
echo ""
echo "📁 log/                     → Runtime log outputs"
echo "│   ├── LogWatcher.log        - Operational logs (start, config, errors)"
echo "│   └── matches.log           - Detected match logs with file and line context"
echo ""
echo "📄 logwatcher.service       → Systemd unit file (auto-installed to /etc/systemd/system)"
echo ""
echo "=========================================================="
echo "⚙️ Service: logwatcher"
echo "• Start   : sudo systemctl start logwatcher"
echo "• Stop    : sudo systemctl stop logwatcher"
echo "• Restart : sudo systemctl restart logwatcher"
echo "• Status  : sudo systemctl status logwatcher"
echo "• Logs    : journalctl -u logwatcher -n 50 --no-pager"
echo ""
echo "📝 To Customize:"
echo "• Change scan interval   → edit 'scan_interval' in config.txt"
echo "• Add patterns           → edit pattern/custompattern"
echo "• Add exclusions         → edit pattern/excluded_lines.txt"
echo ""
echo "🔁 Changes apply automatically on the next scan cycle."
echo "=========================================================="


