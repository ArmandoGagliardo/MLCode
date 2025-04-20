"""
Modulo di training avanzato per modelli di NLP multi-task.

Questo modulo implementa una classe `AdvancedTrainer` per l'addestramento di modelli
di generazione o classificazione di codice e testo, utilizzando funzionalità avanzate:
- Supporto multi-GPU con DataParallel
- Mixed Precision con AMP
- Gradient Accumulation
- Early Stopping
- Scheduler lineare
- Logging dettagliato
- Salvataggio del modello migliore

Compatibile con dataset Hugging Face e tokenizer AutoTokenizer.

Autore:
"""

import torch
from torch.utils.data import DataLoader
from datasets import load_dataset
from transformers import get_scheduler, DataCollatorWithPadding
from tqdm.auto import tqdm
from torch.nn.utils.rnn import pad_sequence


class AdvancedTrainer:
    def __init__(self, model, tokenizer, use_gpu=True):
        """
        Inizializza l'istanza di trainer con il modello, il tokenizer e l'opzione GPU.

        Args:
            model (torch.nn.Module): Il modello da addestrare.
            tokenizer (transformers.PreTrainedTokenizer): Il tokenizer associato.
            use_gpu (bool): Se True usa CUDA se disponibile.
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
        Tokenizza un singolo esempio per task di generazione.

        Args:
            example (dict): Esempio con 'input' e 'output'.

        Returns:
            dict: Dizionario tokenizzato con input_ids, attention_mask e labels.
        """
        tokenized_input = self.tokenizer(
            example["input"], padding="max_length", truncation=True, max_length=128
        )
        tokenized_output = self.tokenizer(
            example["output"], padding="max_length", truncation=True, max_length=128
        )
        tokenized_input["labels"] = tokenized_output["input_ids"]
        return tokenized_input

    def collate_fn(self, batch):
        """
        Funzione collate personalizzata per pad dinamico con PyTorch.

        Args:
            batch (list): Lista di esempi tokenizzati.

        Returns:
            dict: Batch pad-ato con input_ids, attention_mask e labels.
        """
        input_ids = [torch.tensor(x["input_ids"]) for x in batch]
        attention_mask = [torch.tensor(x["attention_mask"]) for x in batch]
        labels = [torch.tensor(x["labels"]) for x in batch]

        return {
            "input_ids": pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id),
            "attention_mask": pad_sequence(attention_mask, batch_first=True, padding_value=0),
            "labels": pad_sequence(labels, batch_first=True, padding_value=-100)
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
        Esegue il ciclo di training completo su un dataset.

        Args:
            dataset_path (str): Percorso al file JSON contenente il dataset.
            output_dir (str): Cartella di output per il modello.
            num_epochs (int): Numero di epoche di addestramento.
            batch_size (int): Dimensione dei batch.
            learning_rate (float): Tasso di apprendimento.
            accumulation_steps (int): Passi per accumulation dei gradienti.
            early_stopping_patience (int): Numero di epoche senza miglioramenti prima di stop.
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

        print("🚀 Inizio training...")

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
            val_loss = self.validate(val_loader)
            print(f"📈 Epoch {epoch+1}: train_loss={avg_train_loss:.4f} | val_loss={val_loss:.4f}")

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
            float: Media delle perdite (loss) su validation set.
        """
        self.model.eval()
        total_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                outputs = self.model(**batch)
                loss = outputs.loss
                loss = loss.mean() if loss.dim() > 0 else loss
                total_loss += loss.item()

        return total_loss / len(val_loader)
