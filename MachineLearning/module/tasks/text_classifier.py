# module/tasks/text_classifier.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class TextClassifier:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)


    def classify(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        pred = torch.argmax(outputs.logits, dim=-1).item()
        return pred