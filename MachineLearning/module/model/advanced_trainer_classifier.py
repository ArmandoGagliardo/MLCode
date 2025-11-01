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

logger = logging.getLogger(__name__)
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
    def __init__(self, model_manager):
        """
        Inizializza il trainer avanzato per classificazione.
        
        Args:
            model_manager: Istanza di ModelManager che contiene modello e tokenizer
        """
        self.tokenizer = model_manager.tokenizer
        self.model = model_manager.get_model()
        self.device = model_manager.device
        
        if torch.cuda.device_count() > 1:
            self.model = torch.nn.DataParallel(self.model)
            logger.info(f"Multi-GPU attivo ({torch.cuda.device_count()} GPU)")
        
        logger.info(f"Trainer inizializzato con modello su device: {self.device}")
        logger.info(f"Tokenizer pronto per l'uso")
        """
        Inizializza il trainer per classificazione.

        Args:
            model (torch.nn.Module): Modello di classificazione.
            tokenizer (PreTrainedTokenizer): Tokenizer associato.
            use_gpu (bool): Se True usa la GPU se disponibile.
        """
        self.model.to(self.device)

        if torch.cuda.device_count() > 1 and self.device.type == "cuda":
            self.model = torch.nn.DataParallel(self.model)
            print(f"✅ Multi-GPU attivo ({torch.cuda.device_count()} GPU)")

        print(f"📍 Device di training: {self.device}")

    def tokenize_example(self, example):
        """
        Tokenizza un esempio per classificazione.

        Args:
            example (dict): Esempio con 'input' e 'output' (label).

        Returns:
            dict: input_ids, attention_mask e labels.
        """
        try:
            # Tokenizza il testo di input
            tokenized = self.tokenizer(
                example["input"],
                padding="max_length",
                truncation=True,
                max_length=128,
                return_tensors=None  # Ritorna liste invece che tensori
            )
            
            # Usa 'output' come etichetta
            label = example.get("output", example.get("label", 0))  # fallback a 'label' o 0
            tokenized["labels"] = int(label) if isinstance(label, str) else label
            
            logger.debug(f"Esempio tokenizzato con successo: input_len={len(tokenized['input_ids'])}, label={tokenized['labels']}")
            return tokenized
            
        except Exception as e:
            logger.error(f"Errore nella tokenizzazione dell'esempio: {e}")
            logger.error(f"Esempio problematico: {example}")
            raise

    def collate_fn(self, batch):
        """
        Collate con padding per classificazione.

        Args:
            batch (list): Lista di esempi tokenizzati.

        Returns:
            dict: input_ids, attention_mask, labels.
        """
        # Converti in tensori in modo ottimizzato
        input_ids = [torch.tensor(x["input_ids"], dtype=torch.long).clone().detach() for x in batch]
        attention_mask = [torch.tensor(x["attention_mask"], dtype=torch.long).clone().detach() for x in batch]
        labels = [torch.tensor(x["labels"], dtype=torch.long).clone().detach() for x in batch]

        # Padding e stacking
        padded_input_ids = pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id)
        padded_attention_mask = pad_sequence(attention_mask, batch_first=True, padding_value=0)
        stacked_labels = torch.stack(labels)

        return {
            "input_ids": padded_input_ids,
            "attention_mask": padded_attention_mask,
            "labels": stacked_labels
        }

    def train_model(
        self,
        dataset_path,
        model_save_path,
        batch_size=4,
        num_epochs=4,
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
        
        # Inizializza GradScaler solo se CUDA è disponibile
        use_amp = torch.cuda.is_available()
        scaler = torch.amp.GradScaler() if use_amp else None
        
        best_val_loss = float("inf")
        patience_counter = 0
        
        logger.info(f"Training config: batch_size={batch_size}, epochs={num_epochs}, lr={learning_rate}")
        logger.info(f"Using mixed precision: {use_amp}")

        print("🚀 Inizio training (classificazione)...")

        progress = tqdm(range(num_epochs * len(train_loader)), desc="Training")

        for epoch in range(num_epochs):
            self.model.train()
            total_loss = 0

            for i, batch in enumerate(train_loader):
                batch = {k: v.to(self.device) for k, v in batch.items()}

                # Context manager per mixed precision training
                with torch.autocast(device_type="cuda" if use_amp else "cpu", enabled=use_amp):
                    outputs = self.model(**batch)
                    loss = outputs.loss
                    loss = loss.mean() if loss.dim() > 0 else loss
                    loss = loss / accumulation_steps

                # Backward pass con o senza GradScaler
                if use_amp:
                    scaler.scale(loss).backward()
                    if (i + 1) % accumulation_steps == 0 or (i + 1) == len(train_loader):
                        scaler.step(optimizer)
                        scaler.update()
                        optimizer.zero_grad()
                        scheduler.step()
                else:
                    loss.backward()
                    if (i + 1) % accumulation_steps == 0 or (i + 1) == len(train_loader):
                        optimizer.step()
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
                self.model.module.save_pretrained(model_save_path) if isinstance(self.model, torch.nn.DataParallel) else self.model.save_pretrained(model_save_path)
                self.tokenizer.save_pretrained(model_save_path)
                logger.info(f"Miglior modello salvato in {model_save_path}")
                print(f"✅ Miglior modello salvato in {model_save_path}")
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
