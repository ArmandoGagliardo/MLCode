# 📁 model_manager.py

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
import torch

class ModelManager:
    def __init__(self, task: str, model_name: str):
        self.task = task
        self.model_name = model_name
        if task == "security_classification":
            self.num_labels = 5
        else:
            self.num_labels = 2

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        if task == "code_generation":
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        elif task in ["text_classification", "security_classification"]:
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=self.num_labels)
        else:
            raise ValueError(f"Task non supportato: {task}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def get_model(self):
        return self.model

    def get_tokenizer(self):
        return self.tokenizer
