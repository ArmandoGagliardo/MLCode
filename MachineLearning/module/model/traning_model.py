import torch
from torch.utils.data import DataLoader
from datasets import load_dataset,Dataset
from torch.nn.utils.rnn import pad_sequence
from transformers import DataCollatorWithPadding,get_scheduler
from torch.optim import AdamW
from tqdm.auto import tqdm

class TrainingModel():
    """
    Classe responsabile dell'addestramento di un modello di machine learning.

    Questa classe gestisce il processo di addestramento, compreso il caricamento del modello, il tokenizer,
    la gestione del dispositivo (CPU o GPU) e la possibilità di utilizzare il parallelismo con più GPU. 
    È possibile eseguire il training su GPU se `use_gpu` è impostato a `True`.

    **Note:**
        - La classe non è ancora stata testata in scenari di produzione con il parallelismo su più GPU.
    
    Args:
        model_manager (object): Un'istanza del gestore del modello responsabile di fornire il modello e il tokenizer.
        use_gpu (bool, optional): Se impostato a `True`, il modello verrà addestrato su GPU (se disponibile). Default: `False`.

    Attributes:
        model_manager (object): L'istanza del gestore del modello.
        tokenizer (Tokenizer): Il tokenizer utilizzato per tokenizzare i dati di input.
        model (nn.Module): Il modello di deep learning che verrà addestrato.
        device (torch.device): Il dispositivo (CPU o GPU) su cui verrà eseguito l'addestramento.
    """
    def __init__(self,model_manager,use_gpu=False):
        """
        Inizializza la classe Training_Class caricando il modello e il tokenizer dal model_manager.
        
        Questa funzione imposta il modello e il tokenizer e trasferisce il modello sul dispositivo
        appropriato (CPU o GPU). Se `use_gpu` è abilitato e sono disponibili più GPU, viene utilizzata 
        la funzione `torch.nn.DataParallel` per eseguire il parallelismo su più dispositivi.

        Args:
            model_manager (object): Il gestore del modello per caricare il modello e il tokenizer.
            use_gpu (bool, optional): Indica se utilizzare la GPU per l'addestramento (se disponibile). Default: `False`.

        Raises:
            Exception: Se ci sono errori durante il caricamento del modello o del tokenizer.
        """
        self._model_manager = model_manager
        self._use_gpu = use_gpu
        # Carica il modello e il tokenizer dal model_manager
        try:
            self._tokenizer = self._model_manager.get_tokenizer()  # Ottenere il tokenizer dal model_manager
            self._model = self._model_manager.get_model()  # Ottenere il modello dal model_manager

            self.set_device()

        except Exception as e:
            print(f"Errore nel caricamento del modello o del tokenizer: {e}")
            exit()              
    
    def update(self,data,file):
        """
        Aggiorna il dataset utilizzato per l'addestramento con nuovi dati e file.

        Args:
            data: I nuovi dati che devono essere aggiunti al dataset.
            file: Il percorso del file che contiene i dati aggiornati.
        """
        self.dataset.update_dataset(data,file)

    def set_device(self):
        # Configura il dispositivo (GPU o CPU)
        self._device = torch.device("cuda" if self._use_gpu and torch.cuda.is_available() else "cpu")
        
        # Sposta il modello sul dispositivo appropriato
        self._model.to(self._device)

        print(f"Device: {self._device} : { torch.cuda.is_available()}")

        # Se più GPU sono disponibili e `use_gpu` è abilitato
        if torch.cuda.device_count() > 1 and self._use_gpu:
            self._model = torch.nn.DataParallel(self._model)  # Utilizza DataParallel per distribuire il lavoro su più GPU
            print(f"Numero di devices: {torch.cuda.device_count()}")

    def validate_model(self,validation_dataloader, model, device):
        """
        Valida il modello su un set di dati di validazione.

        Questa funzione esegue un forward pass sul dataset di validazione senza calcolare
        i gradienti (disabilitando il calcolo dei gradienti). Viene calcolata la perdita media e l'accuratezza
        del modello.

        Args:
            validation_dataloader (DataLoader): Il DataLoader che fornisce i dati di validazione.
            model (torch.nn.Module): Il modello da validare.
            device (torch.device): Il dispositivo (CPU o GPU) su cui eseguire la validazione.

        Returns:
            tuple:
                - avg_val_loss (float): La perdita media calcolata sul dataset di validazione.
                - accuracy (float): L'accuratezza del modello calcolata sul dataset di validazione.
        """
        model.eval()  # Imposta il modello in modalità di valutazione
        total_loss = 0
        correct_predictions = 0
        total_predictions = 0

        with torch.no_grad():  # Disabilita il calcolo dei gradienti

            for batch in validation_dataloader:
                # Sposta il batch sul dispositivo
                if not isinstance(self._model, torch.nn.DataParallel):
                    batch = {k: v.to(self._device) for k, v in batch.items()}
                # Esegui il forward pass
                outputs = model(**batch)
                loss = outputs.loss # Calcola la perdita
                logits = outputs.logits
                if loss.numel() > 1:
                    loss = loss.mean()
                total_loss += loss.item()

                # Calcola le predizioni
                predictions = torch.argmax(logits, dim=-1)  # Trova le predizioni
                correct_predictions += (predictions == batch['labels']).sum().item()  # Calcola le predizioni corrette
                total_predictions += batch['labels'].numel()  # Calcola il numero totale di etichette

        # Calcola la perdita media e l'accuratezza
        avg_val_loss = total_loss / len(validation_dataloader)
        accuracy = correct_predictions / total_predictions

        print(f"Validazione - Perdita Media: {avg_val_loss:.4f}, Accuratezza: {accuracy:.4f}")

        return avg_val_loss, accuracy
            # Applica il padding durante la tokenizzazione

    # Funzione collate personalizzata per gestire il padding dinamico (opzionale, se non si usa max_length)
    def collate_fn(self, batch):
        input_ids = [x["input_ids"] for x in batch]
        attention_mask = [x["attention_mask"] for x in batch]
        labels = [x["labels"] for x in batch]

        input_ids_padded = pad_sequence(input_ids, batch_first=True, padding_value=self._tokenizer.pad_token_id)
        attention_mask_padded = pad_sequence(attention_mask, batch_first=True, padding_value=0)

        # ➕ Adattamento dinamico delle labels
        if isinstance(labels[0], torch.Tensor) and labels[0].dim() > 0:
            # Etichette di tipo sequenza (es. CodeT5 o T5)
            labels_padded = pad_sequence(labels, batch_first=True, padding_value=-100)
        else:
            # Etichette numeriche scalari
            labels_padded = torch.tensor(labels, dtype=torch.long)

        return {
            "input_ids": input_ids_padded,
            "attention_mask": attention_mask_padded,
            "labels": labels_padded
        }
    
    def tokenize_function(self, raw_data):
        # Tokenizza il testo di input (sempre presente)
        tokenized_data = self._tokenizer(
            raw_data["input"],
            padding="max_length",
            truncation=True,
            max_length=128
        )

        # Etichetta: può essere testuale (da tokenizzare) o numerica
        label_key = "output" if "output" in raw_data else "label"
        label = raw_data[label_key]

        # Caso classificazione numerica
        if isinstance(label, int):
            tokenized_data["labels"] = label

        # Caso classificazione con label testuale
        elif isinstance(label, str):
            label_ids = self._tokenizer(
                label,
                padding="max_length",
                truncation=True,
                max_length=128
            )["input_ids"]
            tokenized_data["labels"] = label_ids

        # Caso generazione → già tokenizzato
        elif isinstance(label, list):
            tokenized_data["labels"] = label

        else:
            raise ValueError(f"Formato non supportato per l'etichetta: {type(label)}")

        return tokenized_data
    
    def train_model(self, dataset_path, model_save_path,batch_size, num_epochs, learning_rate,warmup_epochs=5,remove_labes = [""]):
        """
        Addestra il modello utilizzando un dataset personalizzato e salva il modello migliore.

        Questo metodo esegue l'intero processo di addestramento, inclusa la suddivisione dei dati
        in batch, l'esecuzione di più epoche e la regolazione dei pesi del modello. Il modello viene 
        validato periodicamente e viene salvato il miglior modello basato sulla perdita di validazione.

        Args:
            DATASET_FILE: Il dataset utilizzato per l'addestramento del modello.
            model_save_path (str): Il percorso in cui salvare il modello addestrato.
            num_epochs (int): Il numero di epoche di addestramento.
            batch_size (int): La dimensione del batch per l'addestramento.
            learning_rate (float): Il tasso di apprendimento utilizzato per aggiornare i pesi.
            use_gpu (bool, optional): Se impostato a `True`, il modello verrà addestrato su GPU (se disponibile). Default: `False`.

        Returns:
            None
        """

        # Carica il dataset personalizzato dal file JSON
        train_raw_dataset = load_dataset("json", data_files=dataset_path,split="train")


        # Tokenizza il dataset
        tokenized_dataset = train_raw_dataset.map(self.tokenize_function, batched=True)
        # Rimuove le colonne inutili e mantiene solo input_ids e attention_mask per il training
        # Rimuove le colonne inutili in modo dinamico
        columns_to_remove = []
        possible_meta = ["task_type", "func_name", "language", "input", "output"]  # campi non necessari al training

        for col in possible_meta:
            if col in tokenized_dataset.column_names and col not in ["input_ids", "attention_mask", "labels"]:
                columns_to_remove.append(col)

        if columns_to_remove:
            tokenized_dataset = tokenized_dataset.remove_columns(columns_to_remove)

        tokenized_dataset.set_format('torch')

        # Split del dataset per il training e la validazione (80% train, 20% validation)
        tokenized_dataset = tokenized_dataset.train_test_split(test_size=0.1)
        train_dataset = tokenized_dataset["train"]
        val_dataset = tokenized_dataset["test"]

        # Creazione del DataLoader per il training e la validazione
        train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=self.collate_fn)
        val_dataloader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=self.collate_fn)

        # Imposta l'ottimizzatore
        optimizer = torch.optim.AdamW(self._model.parameters(), lr=learning_rate, weight_decay=1e-4)
        
        # Imposta il modello in modalità di training
        self._model.train()
        
        accumulation_steps = 2  # accumula gradienti su 4 passi
        scaler = torch.GradScaler()  # Inizializza lo scaler per gestire i gradienti

        best_val_loss = float('inf')
        patience_counter = 0
        patience = 2 # Numero di epoche da attendere prima di fermarsi
        num_training_steps = num_epochs * len(train_dataloader)
        scheduler =get_scheduler("linear",optimizer=optimizer,num_warmup_steps=0,num_training_steps=num_training_steps)

        progress_bar = tqdm(range(num_training_steps))

        for epoch in range(num_epochs):

            # Addestra il modello
            total_loss = 0

            for i, batch in enumerate(train_dataloader):
      
                if not isinstance(self._model, torch.nn.DataParallel):
                    batch = {k: v.to(self._device) for k, v in batch.items()}

                # Mixed precision con autocast
                with torch.autocast(device_type="cuda" if self._use_gpu else "cpu"):
                    try:
                        outputs = self._model(**batch)
                    except ValueError as e:
                        print(f"Error during model forward pass: {e}")
                        continue 

                if(outputs.loss == "NoneType"):
                    raise ValueError(f"Output Loss is None: {outputs}")
                
                optimizer.zero_grad()
                # Calcola la loss e fai media se necessario (es. DataParallel)
                loss = outputs.loss
                if isinstance(loss, torch.Tensor) and loss.dim() > 0:
                    loss = loss.mean()

                # Applichiamo accumulation
                scalar_loss = loss / accumulation_steps

                # Backpropagation con mixed precision
                scaler.scale(scalar_loss).backward()

            if (i + 1) % accumulation_steps == 0 or (i + 1) == len(train_dataloader):
                scaler.step(optimizer)
                torch.cuda.empty_cache()
                scaler.update()
                optimizer.zero_grad()

                # Libera memoria GPU non utilizzata
                total_loss += scalar_loss  # Aggiorna la perdita totale
                progress_bar.update(1)
           # Calcola la perdita media per l'epoca
            avg_train_loss = total_loss / len(train_dataloader)

            # Validazione alla fine di ogni epoca
            val_loss, val_accuracy = self.validate_model(val_dataloader, self._model, self._device)
            
            print(f'Epoca {epoch+1}/{num_epochs}, Loss di Validazione: {val_loss:.4f}, Accuratezza: {val_accuracy:.4f}, Loss di Addestramento: {avg_train_loss:.4f}')

            # Scheduler step
            scheduler.step()
            torch.cuda.empty_cache()

            # Early Stopping
            if val_loss < best_val_loss:

                best_val_loss = val_loss
                patience_counter = 0

                # Salva il modello migliore
                model_to_save = self._model.module if isinstance(self._model, torch.nn.DataParallel) else self._model

                model_to_save.save_pretrained(model_save_path)
                self._tokenizer.save_pretrained(model_save_path)
                
                print(f"Modello salvato in {model_save_path}.")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print("Early stopping triggered.")
                    break

        print("Training completato.")

