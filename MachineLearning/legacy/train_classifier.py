import os
import json
from datasets import load_dataset, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)
import torch

# Percorsi
PROJECT_PATH = os.getcwd()
DATASET_PATH = os.path.join(PROJECT_PATH, "dataset", "dataset_classification.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_PATH, "model_classification")

# Carica dataset da JSON
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Converti in Hugging Face Dataset
dataset = Dataset.from_list(data)
print(f"✅ Dataset caricato: {len(dataset)} esempi")

# Tokenizer
model_name = "microsoft/codebert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

dataset = dataset.map(tokenize)
dataset = dataset.train_test_split(test_size=0.2)

# Carica modello
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Collator per padding dinamico
collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Args per il training
args = TrainingArguments(
    output_dir=MODEL_SAVE_PATH,
    eval_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=4,
    learning_rate=2e-5,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    save_total_limit=1,
    logging_dir=os.path.join(PROJECT_PATH, "logs"),
    logging_steps=10,
)

# Funzione di valutazione (accuracy)
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = torch.argmax(torch.tensor(logits), dim=1)
    acc = (preds == torch.tensor(labels)).float().mean()
    return {"accuracy": acc.item()}

# Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    tokenizer=tokenizer,
    data_collator=collator,
    compute_metrics=compute_metrics,
)

# Avvia training
trainer.train()
trainer.save_model(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)

print(f"✅ Modello classificazione salvato in {MODEL_SAVE_PATH}")
