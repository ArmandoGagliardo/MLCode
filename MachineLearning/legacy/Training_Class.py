import torch
from torch.utils.data import DataLoader
from .CustomDataset_Class import CustomDataset_Class


class Training_Class():
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
        self.model_manager = model_manager
        self.use_gpu = use_gpu
        # Carica il modello e il tokenizer dal model_manager
        try:
            self.tokenizer = self.model_manager.get_tokenizer()  # Ottenere il tokenizer dal model_manager
            self.model = self.model_manager.get_model()  # Ottenere il modello dal model_manager

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
        self.device = torch.device("cuda" if self.use_gpu and torch.cuda.is_available() else "cpu")
        
        # Sposta il modello sul dispositivo appropriato
        self.model.to(self.device)

        print(f"Device: {self.device} : { torch.cuda.is_available()}")

        # Se più GPU sono disponibili e `use_gpu` è abilitato
        if torch.cuda.device_count() > 1 and self.use_gpu:
            self.model = torch.nn.DataParallel(self.model)  # Utilizza DataParallel per distribuire il lavoro su più GPU
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
                input_ids, output_ids =  batch
                input_ids = input_ids.to(device)
                output_ids = output_ids.to(device)

                # Debug: Stampa le forme degli input e delle etichette
                print(f"Forma input: {input_ids.shape}, Forma output: {output_ids.shape}")
                # Esegui il forward pass
                outputs = model(input_ids=input_ids, labels=output_ids)
                loss = outputs.loss.mean()  # Calcola la perdita media
                logits = outputs.logits
                total_loss += loss # Aggiungi alla perdita totale
                
                # Calcola le predizioni
                predictions = torch.argmax(logits, dim=-1)  # Trova le predizioni
                correct_predictions += (predictions == output_ids).sum().item()  # Calcola le predizioni corrette
                total_predictions += output_ids.numel()  # Calcola il numero totale di etichette

        # Calcola la perdita media e l'accuratezza
        avg_val_loss = total_loss / len(validation_dataloader)
        accuracy = correct_predictions / total_predictions

        print(f"Validazione - Perdita Media: {avg_val_loss:.4f}, Accuratezza: {accuracy:.4f}")

        return avg_val_loss, accuracy
    
    def train_model(self, data, model_save_path, num_epochs, batch_size, learning_rate,warmup_epochs=5):
        """
        Addestra il modello utilizzando un dataset personalizzato e salva il modello migliore.

        Questo metodo esegue l'intero processo di addestramento, inclusa la suddivisione dei dati
        in batch, l'esecuzione di più epoche e la regolazione dei pesi del modello. Il modello viene 
        validato periodicamente e viene salvato il miglior modello basato sulla perdita di validazione.

        Args:
            data: Il dataset utilizzato per l'addestramento del modello.
            model_save_path (str): Il percorso in cui salvare il modello addestrato.
            num_epochs (int): Il numero di epoche di addestramento.
            batch_size (int): La dimensione del batch per l'addestramento.
            learning_rate (float): Il tasso di apprendimento utilizzato per aggiornare i pesi.
            use_gpu (bool, optional): Se impostato a `True`, il modello verrà addestrato su GPU (se disponibile). Default: `False`.

        Returns:
            None
        """

        # Carica i dati nel dataset personalizzato
        #self.dataset = CustomDataset_Class(data,self.model_manager,self.model_manager.labels)
        self.dataset = CustomDataset_Class(data,self.model_manager,self.model_manager.labels)
        # Crea il DataLoader per il batching
        #dataloader = DataLoader(self.dataset, batch_size=batch_size, shuffle=False, collate_fn=self.dataset.collate_fn)
        dataloader = DataLoader(self.dataset, batch_size=batch_size, shuffle=False, collate_fn=self.dataset.collate_fn)
        # Imposta l'ottimizzatore
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)
        
        # Imposta il modello in modalità di training
        self.model.train()
        
        accumulation_steps = 4  # accumula gradienti su 4 passi
        scaler = torch.GradScaler()  # Inizializza lo scaler per gestire i gradienti

        best_val_loss = float('inf')
        patience_counter = 0
        patience = 5  # Numero di epoche da attendere prima di fermarsi

        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2)

        for epoch in range(num_epochs):

            # Aumento del tasso di apprendimento per warm-up
            if epoch < warmup_epochs:
                lr = learning_rate * (epoch + 1) / warmup_epochs
                for param_group in optimizer.param_groups:
                    param_group['lr'] = lr
            else:
                lr = learning_rate  # Usa il tasso di apprendimento predefinito

            print(f"Epoch {epoch + 1}/{num_epochs}, Learning Rate: {lr:.6f}")
            # Addestra il modello
            total_loss = 0

            optimizer.zero_grad()  # Azzerare i gradienti

            for i, (input_ids, output_ids) in enumerate(dataloader):

                print(f"Batch {i}:")
                print(f"Input IDs shape: {input_ids.shape}")  # Dovrebbe essere (batch_size, sequence_length)
                print(f"Output IDs shape: {output_ids.shape}")  # Dovrebbe essere (batch_size, sequence_length)

                # Verifica se il batch è corretto
                if input_ids.shape[0] != output_ids.shape[0]:
                    print(f"Dimension mismatch in batch {i}: Input {input_ids.shape[0]} vs Output {output_ids.shape[0]}")
                if input_ids.shape[1] != self.model_manager.MAX_LENGTH or output_ids.shape[1] != self.model_manager.MAX_LENGTH:
                    print(f"Dimension mismatch in batch {i}: Input length {input_ids.shape[1]} vs Output length {output_ids.shape[1]}")

                if input_ids is None or output_ids is None:
                    print(f"Skipping batch {i} due to None values.")
                    continue

                assert input_ids.shape[0] == output_ids.shape[0], "Mismatch between input and output batch sizes"
                assert input_ids.shape[1] == self.model_manager.MAX_LENGTH, "Input sequence length mismatch"
                assert output_ids.shape[1] == self.model_manager.MAX_LENGTH, "Output sequence length mismatch"
                
                # Sposta i tensori su GPU o CPU
                input_ids = input_ids.to(self.device)
                output_ids = output_ids.to(self.device)

                
                # Controlla le dimensioni prima di passare al modello
                if input_ids.shape[0] != output_ids.shape[0]:
                    print(f"Dimension mismatch: Input IDs {input_ids.shape[0]} vs Output IDs {output_ids.shape[0]}")
                    exit()

                # Mixed precision con autocast
                with torch.autocast(device_type="cuda" if self.use_gpu else "cpu"):
                    try:
                        outputs = self.model(input_ids=input_ids, labels=output_ids)
                    except ValueError as e:
                        print(f"Error during model forward pass: {e}")
                        continue 

                    loss = outputs.loss.mean() / accumulation_steps # Calcola la perdita media .mean()
                    print(f'Loss shape: {loss.shape}')  # Aggiungi questa riga
                # Controlla se la perdita è uno scalare
                if loss.numel() != 1:
                    raise ValueError(f"Loss is not a scalar: {loss}")
                # Backpropagation usando GradScaler per mixed precision
                scaler.scale(loss).backward()  # Calcola i gradienti

                # Esegui il passo dell'ottimizzatore ogni 'accumulation_steps'
                if (i + 1) % accumulation_steps == 0  or (i + 1) == len(dataloader):
                    scaler.step(optimizer)  # Aggiorna i pesi
                    scaler.update()  # Aggiorna lo scaler per la prossima iterazione
                    optimizer.zero_grad()  # Azzerare i gradienti

                # Libera memoria GPU non utilizzata
                total_loss += loss  # Aggiorna la perdita totale

           # Calcola la perdita media per l'epoca
            avg_train_loss = total_loss / len(dataloader)
            print(f'Epoca {epoch+1}/{num_epochs}, Loss di Addestramento: {avg_train_loss:.4f}')

            # Validazione alla fine di ogni epoca
            val_loss, val_accuracy = self.validate_model(dataloader, self.model, self.device)
            print(f'Epoca {epoch+1}/{num_epochs}, Loss di Validazione: {val_loss:.4f}, Accuratezza: {val_accuracy:.4f}')

            # Scheduler step
            scheduler.step(val_loss)
            torch.cuda.empty_cache()

            # Early Stopping
            if val_loss < best_val_loss:

                best_val_loss = val_loss
                patience_counter = 0

                # Salva il modello migliore
                model_to_save = self.model.module if isinstance(self.model, torch.nn.DataParallel) else self.model

                model_to_save.save_pretrained(model_save_path, safe_serialization=False)
                self.tokenizer.save_pretrained(model_save_path, safe_serialization=False)
                
                print(f"Modello salvato in {model_save_path}.")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print("Early stopping triggered.")
                    break

        print("Training completato.")
