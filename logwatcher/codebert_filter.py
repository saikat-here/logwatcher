import os
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

# Load tokenizer and model structure
MODEL_NAME = "microsoft/codebert-base"
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
model = RobertaForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

# Load fine-tuned weights from safetensors
BASE_DIR = "/opt/LogWatcher/"  # Must match the path used in LogWatcher.py
MODEL_FILE = os.path.join(BASE_DIR,"model", "model.safetensors")
state_dict = torch.load(MODEL_FILE, map_location=torch.device("cpu"))
model.load_state_dict(state_dict)
model.eval()


def classify_line(text: str) -> str:
    """
    Classify a log line as 'true_positive' or 'false_positive'.
    Returns one of the two labels as a string.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)
        predicted_label = torch.argmax(probs, dim=1).item()

    return "true_positive" if predicted_label == 1 else "false_positive"
