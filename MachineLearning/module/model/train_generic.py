# 📁 train_generic.py
import json
import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
from module.model.traning_model import TrainingModel
from module.model.model_manager import ModelManager


class GenericTrainer:
    def __init__(self, model_path, task_type, num_labels=2):
        self.task_type = task_type
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.multi_gpu = torch.cuda.device_count() > 1

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        if task_type == "code_generation":
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        elif task_type in ["text_classification", "security_classification"]:
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=num_labels)
        else:
            raise ValueError(f"Task non supportato: {task_type}")

        if self.multi_gpu:
            self.model = torch.nn.DataParallel(self.model)

        self.model.to(self.device)

    def load_dataset(self, dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = Dataset.from_list(data)
        return dataset.train_test_split(test_size=0.2)

    def tokenize(self, example):
        if self.task_type == "code_generation":
            input_enc = self.tokenizer(
                example["input"], padding="max_length", truncation=True, max_length=128, return_tensors=None
            )
            output_enc = self.tokenizer(
                example["output"], padding="max_length", truncation=True, max_length=128, return_tensors=None
            )
            return {
                "input_ids": input_enc["input_ids"],
                "attention_mask": input_enc["attention_mask"],
                "labels": output_enc["input_ids"]
            }
        else:
            enc = self.tokenizer(
                example["input"], padding="max_length", truncation=True, max_length=128, return_tensors=None
            )
            # output può essere numerico (per classificazione)
            return {
                "input_ids": enc["input_ids"],
                "attention_mask": enc["attention_mask"],
                "labels": example.get("label", example["output"])  # fallback se "label" non c'è
            }

    def compute_metrics(self, eval_pred):
        logits, labels = eval_pred
        preds = torch.argmax(torch.tensor(logits), dim=1)
        acc = (preds == torch.tensor(labels)).float().mean()
        return {"accuracy": acc.item()}

    def train(self, dataset_path, output_dir="model_output", num_epochs=4):
        if self.task_type == "code_generation":
            print("🚀 Addestramento con TrainingModel (custom)...")
            model_manager = ModelManager(self.model, self.tokenizer)
            trainer = TrainingModel(model_manager, use_gpu=torch.cuda.is_available())

            trainer.train_model(
                dataset_path=dataset_path,
                model_save_path=output_dir,
                batch_size=1,
                num_epochs=num_epochs,
                learning_rate=2e-5,
                remove_labes=["task_type", "func_name", "language"]
            )
            return

        print("🚀 Addestramento con HuggingFace Trainer...")
        dataset = self.load_dataset(dataset_path)
        dataset = dataset.map(self.tokenize)

        args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            num_train_epochs=num_epochs,
            logging_dir="logs",
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            gradient_accumulation_steps=1,
            remove_unused_columns=False,
            fp16=False,
            ddp_find_unused_parameters=False if self.multi_gpu else None
        )

        trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics
        )

        trainer.train()
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        print(f"✅ Modello salvato in {output_dir}")
