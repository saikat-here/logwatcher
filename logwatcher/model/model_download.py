from huggingface_hub import hf_hub_download
import os
import shutil

model_path = hf_hub_download(
    repo_id="saikat100/cvbert",
    filename="model.safetensors"
)

os.makedirs("logwatcher/model", exist_ok=True)
shutil.copy(model_path, "model.safetensors")
print("✅ Model downloaded")
