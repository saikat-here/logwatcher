from huggingface_hub import hf_hub_download
import os
import shutil

BASE_DIR = "/opt/LogWatcher"
destination_dir = os.path.join(BASE_DIR, "model")
destination_file = os.path.join(destination_dir, "model.safetensors")

print(f"Downloading the model at: {destination_dir}")
os.makedirs(destination_dir, exist_ok=True)

model_path = hf_hub_download(
    repo_id="saikat100/cvbert",
    filename="model.safetensors"
)
print("Hugging Face cached path:", model_path)

shutil.copy(model_path, destination_file)
print("Copied to:", destination_file)

if os.path.exists(destination_file):
    print("✅ Model downloaded successfully.")
else:
    print("❌ Model not found after copy.")
