import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
import numpy as np
import os
import json

LABELS = {
    "medical": 0,
    "legal": 1,
    "finance": 2,
    "sports": 3,
    "culture": 4,
    "crime": 5,
    "world": 6,
    "news": 7,
    "hystory": 8,
    "science": 9,
    "grammar": 10,
    "literature": 11,
    "religion": 12,
    "education": 13,
    "philosophy": 14,
    "fantasy": 15,
    "tech": 16,
    "mythology": 17,
    "nature": 18,
    "narrative": 19,
    "book": 20
}

class TextClassifierSupervised:
    def __init__(self, model_name="dbmdz/bert-base-italian-cased", model_path="models/text_classifier"):
        self.label2id = LABELS
        self.id2label = {v: k for k, v in LABELS.items()}
        self.model_name = model_name
        self.model_path = model_path

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        if os.path.exists(model_path):
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        else:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, num_labels=len(self.label2id), id2label=self.id2label, label2id=self.label2id
            )

    def preprocess(self, examples):
        return self.tokenizer(examples['text'], truncation=True, padding=True, max_length=512)

    def predict(self, text, threshold=0.5):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).numpy()[0]

        max_idx = int(np.argmax(probs))
        max_score = float(probs[max_idx])

        if max_score >= threshold:
            return self.id2label[max_idx], max_score
        else:
            return "uncertain", max_score

    def train(self, examples):
        # examples: list of dicts with 'text' and 'label' (string)
        texts = [ex['text'] for ex in examples if ex['label'] in self.label2id]
        labels = [self.label2id[ex['label']] for ex in examples if ex['label'] in self.label2id]

        dataset = Dataset.from_dict({"text": texts, "label": labels})
        dataset = dataset.train_test_split(test_size=0.1)

        tokenized = dataset.map(self.preprocess, batched=True)

        training_args = TrainingArguments(
            output_dir="tmp/text_cls", evaluation_strategy="epoch", per_device_train_batch_size=8,
            per_device_eval_batch_size=8, num_train_epochs=4, save_steps=200, logging_steps=50,
            load_best_model_at_end=True, save_total_limit=2, metric_for_best_model="accuracy"
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["test"],
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics
        )

        trainer.train()
        self.model.save_pretrained(self.model_path)

    def compute_metrics(self, eval_pred):
        from sklearn.metrics import accuracy_score, f1_score
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_score(labels, preds),
            "f1": f1_score(labels, preds, average="macro")
        }

    def build_dataset_from_jsonl(self, jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        examples = []
        for line in lines:
            try:
                item = json.loads(line)
                if 'text' in item and 'label' in item:
                    examples.append({"text": item["text"], "label": item["label"]})
            except json.JSONDecodeError:
                continue

        return examples
