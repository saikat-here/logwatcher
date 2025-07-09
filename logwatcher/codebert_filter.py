import os
import torch
from safetensors.torch import load_file  # <-- this is the correct way
from transformers import RobertaTokenizer, RobertaForSequenceClassification

MODEL_NAME = "microsoft/codebert-base"
BASE_DIR = "/opt/LogWatcher"
MODEL_PATH = os.path.join(BASE_DIR, "model", "model.safetensors")

# Load tokenizer and model architecture
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
model = RobertaForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

# Load safetensors weights safely
state_dict = load_file(MODEL_PATH)
model.load_state_dict(state_dict)
model.eval()


def classify_line(text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted = torch.argmax(torch.softmax(logits, dim=1), dim=1).item()
    return "true_positive" if predicted == 1 else "false_positive"
