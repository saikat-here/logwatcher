from huggingface_hub import hf_hub_download
import os
import shutil
import sys

model_path = hf_hub_download(
    repo_id="saikat100/cvbert",
    filename="model.safetensors"
)
model_dir = os.path.join("/opt/LogWatcher","model")

print(f"Downloading the model at: {model_dir} ")
os.makedirs(model_dir, exist_ok=True)
shutil.copy(model_path, "model.safetensors")
print("✅ Model downloaded")
