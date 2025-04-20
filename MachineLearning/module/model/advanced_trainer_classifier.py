"""
Modulo di training avanzato per modelli di classificazione.

Questa versione di trainer è pensata per task di classificazione NLP come:
- classificazione binaria
- classificazione multi-classe

Caratteristiche principali:
- Supporto multi-GPU (DataParallel)
- Mixed Precision (AMP)
- Gradient Accumulation
- Early Stopping
- Scheduler lineare
- Logging su file
- Salvataggio del modello migliore

Autore: 
"""

import torch
import logging
from torch.utils.data import DataLoader
from datasets import load_dataset
from transformers import get_scheduler
from tqdm.auto import tqdm
from torch.nn.utils.rnn import pad_sequence


# 🔧 Logging su file
logging.basicConfig(
    filename="training_classifier.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class AdvancedTrainerClassifier:
    def __init__(self, model, tokenizer, use_gpu=True):
        """
        Inizializza il trainer per classificazione.

        Args:
            model (torch.nn.Module): Modello di classificazione.
            tokenizer (PreTrainedTokenizer): Tokenizer associato.
            use_gpu (bool): Se True usa la GPU se disponibile.
        """
        self.tokenizer = tokenizer
        self.model = model
        self.use_gpu = use_gpu
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.model.to(self.device)

        if torch.cuda.device_count() > 1 and self.use_gpu:
            self.model = torch.nn.DataParallel(self.model)
            print(f"✅ Multi-GPU attivo ({torch.cuda.device_count()} GPU)")

        print(f"📍 Device di training: {self.device}")

    def tokenize_example(self, example):
        """
        Tokenizza un esempio per classificazione.

        Args:
            example (dict): Esempio con 'input' e 'label'.

        Returns:
            dict: input_ids, attention_mask e labels.
        """
        tokenized = self.tokenizer(
            example["input"],
            padding="max_length",
            truncation=True,
            max_length=128
        )
        tokenized["labels"] = int(example["label"]) if isinstance(example["label"], str) else example["label"]
        return tokenized

    def collate_fn(self, batch):
        """
        Collate con padding per classificazione.

        Args:
            batch (list): Lista di esempi tokenizzati.

        Returns:
            dict: input_ids, attention_mask, labels.
        """
        input_ids = [torch.tensor(x["input_ids"]) for x in batch]
        attention_mask = [torch.tensor(x["attention_mask"]) for x in batch]
        labels = [torch.tensor(x["labels"]) for x in batch]

        return {
            "input_ids": pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id),
            "attention_mask": pad_sequence(attention_mask, batch_first=True, padding_value=0),
            "labels": torch.stack(labels)
        }

    def train(
        self,
        dataset_path,
        output_dir,
        num_epochs=4,
        batch_size=4,
        learning_rate=5e-5,
        accumulation_steps=2,
        early_stopping_patience=2
    ):
        """
        Esegue il ciclo di training su un dataset JSON.

        Args:
            dataset_path (str): Percorso al file JSON.
            output_dir (str): Cartella per salvare il modello.
            num_epochs (int): Epoche totali.
            batch_size (int): Dimensione dei batch.
            learning_rate (float): Learning rate.
            accumulation_steps (int): Accumulo gradiente.
            early_stopping_patience (int): Epoche di tolleranza senza miglioramento.
        """
        print("📚 Caricamento dataset...")
        dataset = load_dataset("json", data_files=dataset_path, split="train")
        dataset = dataset.map(self.tokenize_example)
        dataset.set_format("torch")
        dataset = dataset.train_test_split(test_size=0.2)
        train_dataset, val_dataset = dataset["train"], dataset["test"]

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=self.collate_fn)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=self.collate_fn)

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=0,
                                  num_training_steps=num_epochs * len(train_loader))
        scaler = torch.amp.GradScaler()

        best_val_loss = float("inf")
        patience_counter = 0

        print("🚀 Inizio training (classificazione)...")

        progress = tqdm(range(num_epochs * len(train_loader)), desc="Training")

        for epoch in range(num_epochs):
            self.model.train()
            total_loss = 0

            for i, batch in enumerate(train_loader):
                batch = {k: v.to(self.device) for k, v in batch.items()}

                with torch.autocast(device_type="cuda" if self.device.type == "cuda" else "cpu"):
                    outputs = self.model(**batch)
                    loss = outputs.loss
                    loss = loss.mean() if loss.dim() > 0 else loss

                scaler.scale(loss / accumulation_steps).backward()

                if (i + 1) % accumulation_steps == 0 or (i + 1) == len(train_loader):
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()
                    scheduler.step()

                total_loss += loss.item()
                progress.update(1)

            avg_train_loss = total_loss / len(train_loader)
            val_loss, val_acc = self.validate(val_loader)
            print(f"📈 Epoch {epoch+1}: train_loss={avg_train_loss:.4f} | val_loss={val_loss:.4f} | acc={val_acc:.4f}")
            logging.info(f"Epoch {epoch+1}: train_loss={avg_train_loss:.4f} | val_loss={val_loss:.4f} | acc={val_acc:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                self.model.module.save_pretrained(output_dir) if isinstance(self.model, torch.nn.DataParallel) else self.model.save_pretrained(output_dir)
                self.tokenizer.save_pretrained(output_dir)
                print(f"✅ Miglior modello salvato in {output_dir}")
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print("🛑 Early stopping attivato.")
                    break

    def validate(self, val_loader):
        """
        Valida il modello su validation set.

        Args:
            val_loader (DataLoader): Dataloader di validazione.

        Returns:
            tuple: media loss, accuratezza
        """
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                outputs = self.model(**batch)
                loss = outputs.loss
                logits = outputs.logits

                loss = loss.mean() if loss.dim() > 0 else loss
                total_loss += loss.item()

                preds = torch.argmax(logits, dim=-1)
                correct += (preds == batch["labels"]).sum().item()
                total += batch["labels"].size(0)

        return total_loss / len(val_loader), correct / total
