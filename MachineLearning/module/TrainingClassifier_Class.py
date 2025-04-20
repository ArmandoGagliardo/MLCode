import os
import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)
import torch

class TrainingClassifier_Class:
    def __init__(self, model_name="microsoft/codebert-base", model_save_path="model_classification"):
        self.model_name = model_name
        self.model_save_path = model_save_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    def load_dataset(self, path_to_json):
        with open(path_to_json, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        dataset = Dataset.from_list(raw_data)
        dataset = dataset.map(self.tokenize)
        return dataset.train_test_split(test_size=0.2)

    def tokenize(self, batch):
        return self.tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

    def compute_metrics(self, eval_pred):
        logits, labels = eval_pred
        preds = torch.argmax(torch.tensor(logits), dim=1)
        acc = (preds == torch.tensor(labels)).float().mean()
        return {"accuracy": acc.item()}

    def train(self, dataset_path, num_epochs=4, batch_size=4, learning_rate=2e-5):
        dataset = self.load_dataset(dataset_path)
        collator = DataCollatorWithPadding(tokenizer=self.tokenizer)

        args = TrainingArguments(
            output_dir=self.model_save_path,
            eval_strategy="epoch",
            save_strategy="epoch",
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
            save_total_limit=1,
            logging_dir="logs",
            logging_steps=10,
        )

        trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            tokenizer=self.tokenizer,
            data_collator=collator,
            compute_metrics=self.compute_metrics,
        )

        trainer.train()
        trainer.save_model(self.model_save_path)
        self.tokenizer.save_pretrained(self.model_save_path)
        print(f"✅ Modello classificatore salvato in: {self.model_save_path}")
