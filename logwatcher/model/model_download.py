from huggingface_hub import snapshot_download
import os
import shutil

# Set base and destination directory
BASE_DIR = "/opt/LogWatcher"
destination_dir = os.path.join(BASE_DIR, "model")
os.makedirs(destination_dir, exist_ok=True)

print(f"📥 Downloading all model files into: {destination_dir}")

# Download all files from the model repo
model_dir = snapshot_download(
    repo_id="saikat100/cvbert",
    repo_type="model",
    local_dir=destination_dir,
    local_dir_use_symlinks=False  # ensures actual files are copied
)

print("✅ All files downloaded to:", model_dir)

# Optional: Confirm key files
expected = os.path.join(destination_dir, "model.safetensors")
if os.path.exists(expected):
    print("✅ model.safetensors exists.")
else:
    print("⚠️ model.safetensors not found.")
