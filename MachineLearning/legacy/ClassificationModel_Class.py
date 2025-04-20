from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from ModelManager_Class import ModelManager
from module.Training_Class import Training_Class

class ClassificationModel_Class:
    def __init__(self, model_path="model_classification"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

    def classify(self, input_text):
        inputs = self.tokenizer(input_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)

        predicted_class = torch.argmax(outputs.logits, dim=-1).item()
        return "code" if predicted_class == 1 else "text"