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
import logging

logger = logging.getLogger(__name__)


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
        
        # Set pad_token if not already set (required for batch padding)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info(f"[TOKENIZER] Set pad_token to eos_token: {self.tokenizer.eos_token}")
        
        self.model = model
        self.use_gpu = use_gpu
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.model.to(self.device)

        if torch.cuda.device_count() > 1 and self.use_gpu:
            self.model = torch.nn.DataParallel(self.model)
            print(f"[OK] Multi-GPU attivo ({torch.cuda.device_count()} GPU)")

        print(f"[DEVICE] Training device: {self.device}")

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
        # Use clone().detach() to avoid tensor construction warnings
        input_ids = [x["input_ids"].clone().detach() if isinstance(x["input_ids"], torch.Tensor) 
                     else torch.tensor(x["input_ids"]) for x in batch]
        attention_mask = [x["attention_mask"].clone().detach() if isinstance(x["attention_mask"], torch.Tensor)
                          else torch.tensor(x["attention_mask"]) for x in batch]
        labels = [x["labels"].clone().detach() if isinstance(x["labels"], torch.Tensor)
                  else torch.tensor(x["labels"]) for x in batch]

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
        print("[DATASET] Loading dataset...")
        
        # Validate JSON format before loading
        try:
            import json
            from pathlib import Path
            
            dataset_file = Path(dataset_path)
            if not dataset_file.exists():
                raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
            
            # Check file is not empty
            if dataset_file.stat().st_size == 0:
                raise ValueError(f"Dataset file is empty: {dataset_path}")
            
            # Validate JSON format by attempting to parse first
            with open(dataset_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if not first_line.strip():
                    raise ValueError(f"Dataset file appears to be empty or corrupted")
                
                # Try to parse first line as JSON
                try:
                    json.loads(first_line)
                except json.JSONDecodeError:
                    # If not JSONL, check if it's a JSON array
                    f.seek(0)
                    try:
                        json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON format in dataset: {e}")
            
            print("[OK] Dataset file validation passed")
            
        except Exception as e:
            print(f"[FAIL] Dataset validation failed: {e}")
            raise
        
        # Load dataset using HuggingFace datasets library
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

        print("[TRAIN] Starting training...")

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
                
                # Check disk space before saving model
                try:
                    import shutil
                    from pathlib import Path
                    
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    disk_usage = shutil.disk_usage(output_dir)
                    free_space_gb = disk_usage.free / (1024 ** 3)
                    
                    # Require at least 5GB free space
                    if free_space_gb < 5.0:
                        logger.warning(f"Low disk space: {free_space_gb:.2f}GB available")
                        print(f"⚠️ Low disk space: {free_space_gb:.2f}GB available (minimum 5GB recommended)")
                        print(f"   Saving model anyway, but consider freeing disk space")
                    
                    self.model.module.save_pretrained(output_dir) if isinstance(self.model, torch.nn.DataParallel) else self.model.save_pretrained(output_dir)
                    self.tokenizer.save_pretrained(output_dir)
                    print(f"[OK] Best model saved to {output_dir}")
                    
                except OSError as e:
                    logger.error(f"Failed to save model: {e}")
                    print(f"[FAIL] Failed to save model: {e}")
                    print("   Check disk space and permissions")
                    
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print("[STOP] Early stopping activated.")
                    break

    def validate(self, val_dataset=None, val_loader=None, batch_size=4):
        """
        Valida il modello su validation set.

        Args:
            val_dataset: Dataset di validazione (HuggingFace Dataset)
            val_loader (DataLoader): Dataloader di validazione (alternativo a val_dataset)
            batch_size (int): Dimensione del batch (se si usa val_dataset)

        Returns:
            float: Media delle perdite (loss) su validation set.
        """
        # Create dataloader if dataset is provided
        if val_dataset is not None and val_loader is None:
            tokenized_dataset = val_dataset.map(self.tokenize_example)
            tokenized_dataset.set_format("torch")
            val_loader = DataLoader(
                tokenized_dataset,
                batch_size=batch_size,
                shuffle=False,
                collate_fn=self.collate_fn
            )
        
        if val_loader is None:
            raise ValueError("Either val_dataset or val_loader must be provided")
        
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

    def train_one_epoch(self, train_dataset, batch_size=4, learning_rate=5e-5):
        """
        Esegue una singola epoca di training.
        
        Args:
            train_dataset: Dataset di training (HuggingFace Dataset)
            batch_size (int): Dimensione del batch
            learning_rate (float): Learning rate
            
        Returns:
            float: Media della loss dell'epoca
        """
        logger.info(f"[TRAIN] Starting train_one_epoch with {len(train_dataset)} examples")
        
        # Tokenize and prepare dataset
        logger.info("[TRAIN] Tokenizing dataset...")
        tokenized_dataset = train_dataset.map(self.tokenize_example)
        tokenized_dataset.set_format("torch")
        logger.info(f"[TRAIN] Dataset tokenized: {len(tokenized_dataset)} examples")
        
        # Create dataloader
        train_loader = DataLoader(
            tokenized_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=self.collate_fn
        )
        logger.info(f"[TRAIN] DataLoader created with batch_size={batch_size}, {len(train_loader)} batches")
        
        # Setup optimizer if not exists
        if not hasattr(self, 'optimizer'):
            self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
            logger.info(f"[TRAIN] Optimizer created with lr={learning_rate}")
        
        # Training loop
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        logger.info("[TRAIN] Starting training loop...")
        try:
            for batch_idx, batch in enumerate(tqdm(train_loader, desc="Training")):
                try:
                    logger.info(f"[TRAIN] Processing batch {batch_idx + 1}/{len(train_loader)}")
                    logger.info(f"[TRAIN] Batch keys: {batch.keys()}")
                    logger.info(f"[TRAIN] Batch shapes: {[(k, v.shape) for k, v in batch.items()]}")
                    
                    # Move batch to device
                    batch = {k: v.to(self.device) for k, v in batch.items()}
                    logger.info(f"[TRAIN] Batch moved to device: {self.device}")
                    
                    self.optimizer.zero_grad()
                    logger.info("[TRAIN] Gradients zeroed")
                    
                    # Forward pass
                    logger.info("[TRAIN] Starting forward pass...")
                    with torch.autocast(device_type="cuda" if self.device.type == "cuda" else "cpu", enabled=False):
                        outputs = self.model(**batch)
                        loss = outputs.loss
                    logger.info(f"[TRAIN] Forward pass complete, loss: {loss.item():.4f}")
                    
                    # Handle multi-dimensional loss
                    loss = loss.mean() if loss.dim() > 0 else loss
                    logger.info("[TRAIN] Starting backward pass...")
                    
                    # Backward pass
                    loss.backward()
                    logger.info("[TRAIN] Backward pass complete")
                    
                    self.optimizer.step()
                    logger.info("[TRAIN] Optimizer step complete")
                    
                    total_loss += loss.item()
                    num_batches += 1
                    logger.info(f"[TRAIN] Batch {batch_idx + 1} complete, loss: {loss.item():.4f}")
                    
                except Exception as batch_error:
                    logger.error(f"[TRAIN] Error in batch {batch_idx + 1}: {batch_error}", exc_info=True)
                    raise
                    
        except Exception as train_error:
            logger.error(f"[TRAIN] Training loop error: {train_error}", exc_info=True)
            raise
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        logger.info(f"[TRAIN] Epoch completed: {num_batches} batches, avg_loss={avg_loss:.4f}")
        return avg_loss

