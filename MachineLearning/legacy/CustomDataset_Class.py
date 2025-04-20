from torch.utils.data import Dataset
from torch.nn.utils.rnn import pad_sequence
import os,json
import torch

class CustomDataset_Class(Dataset):
    """
    Classe per gestire un dataset personalizzato per l'addestramento di modelli di machine learning.

    La classe supporta il caricamento di dati da un file JSON o da un dizionario. I dati contengono descrizioni
    e frammenti di codice, che vengono tokenizzati utilizzando il tokenizer fornito dal `model_manager`. 
    Il dataset è strutturato per essere utilizzato con PyTorch DataLoader.

    Args:
        data (str or list or dict): Dati di input, che possono essere:
            - Un percorso a un file JSON contenente le descrizioni e i codici.
            - Una lista di dizionari, ciascuno con una descrizione e un frammento di codice.
            - Un dizionario con descrizioni e codici associati a specifiche funzioni.
        model_manager (object): Un'istanza di ModelManager che fornisce il tokenizer per tokenizzare i dati.
    
    Attributes:
        tokenizer (Tokenizer): Il tokenizer utilizzato per convertire il testo in ID di token.
        inputs (list): Lista delle descrizioni tokenizzate.
        outputs (list): Lista dei frammenti di codice tokenizzati.
    """
    def __init__(self, data,model_manager,labels):
        """
        Inizializza il dataset personalizzato caricando e strutturando i dati.

        Controlla se i dati sono forniti come file JSON o dizionario, e li elabora
        di conseguenza. I dati vengono tokenizzati e preparati per l'addestramento.

        Args:
            data (str or dict): I dati da cui creare il dataset. Può essere un percorso a un file JSON,
                                         o un dizionario.
            model_manager (object): Il gestore del modello che fornisce il tokenizer per la tokenizzazione dei dati.

        Raises:
            ValueError: Se il formato dei dati non è né un file JSON, né una lista, né un dizionario.
        """
        self.tokenizer = model_manager.get_tokenizer()
        self.MAX_LENGTH = model_manager.MAX_LENGTH
        self.inputs, self.outputs = [], []
        self.item = {}

        # Controlla se `data` è un file o una lista
        if isinstance(data, str) and os.path.exists(data):
            # Carica il file JSON
            with open(data, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
            # Crea liste di descrizioni e codici
            self.inputs = [func_info['docstring'] for func_info in data.values()]
            self.outputs = [func_info['code'] for func_info in data.values()]
            self.item = [(func_info['docstring'], func_info['language']) for func_info in data.values()]

        elif isinstance(data,dict):
            # Assicurati che le liste siano inizializzate
            self.inputs = [func_info['docstring'] for func_name, func_info in data.items()]
            self.outputs = [func_info['code'] for func_name, func_info in data.items()]
            self.item = [ (func_info['code_tokens'],func_info['func_name'],func_info['language'],func_info['original_string']) for func_name, func_info in data.items()]

        else:
            raise ValueError("Data must be a JSON file path or a dictionaries.")

    def __len__(self):
        """
        Restituisce la lunghezza del dataset.

        Returns:
            int: Il numero di elementi nel dataset (pari al numero di descrizioni/codici).
        """
        return len(self.inputs)
    
    def __getitem__(self, idx):
        """
        Restituisce un elemento del dataset, tokenizzato e convertito in tensori.

        Per un determinato indice, vengono tokenizzate sia la descrizione (input) che il codice (output),
        e convertite in tensori PyTorch.

        Args:
            idx (int): L'indice dell'elemento da restituire.

        Returns:
            tuple: Una tupla contenente due tensori:
                - input_ids_tensor (torch.Tensor): La sequenza tokenizzata della descrizione.
                - output_ids_tensor (torch.Tensor): La sequenza tokenizzata del codice.

        Raises:
            Exception: Se si verifica un errore durante il recupero dell'elemento.
        """
        try:
            # Ottieni la sequenza di input e l'etichetta
            input_sequence = self.inputs[idx]  # Adatta in base alla tua struttura dati
            output_sequence = self.outputs[idx]  # Adatta in base alla tua struttura dati
            # Tokenizza le sequenze
            input_ids = self.tokenizer.encode(input_sequence, max_length=self.MAX_LENGTH, padding='max_length', truncation=True)
            output_ids = self.tokenizer.encode(output_sequence, max_length=self.MAX_LENGTH, padding='max_length', truncation=True)

            # Converte in tensori
            input_ids_tensor = torch.tensor(input_ids)
            output_ids_tensor = torch.tensor(output_ids)

            print(f"__getitem__ index: {idx}, Input IDs shape: {input_ids_tensor.shape}, Output IDs shape: {output_ids_tensor.shape}")

            return input_ids_tensor, output_ids_tensor
            
        except Exception as e:
            print(f"Error in __getitem__ at index {idx}: {str(e)}")
            return torch.tensor([]), torch.tensor([])  # Restituisce tensori vuoti

    def collate_fn(self,batch):
        """
        Funzione di raggruppamento (collate_fn) per preparare un batch di dati.

        Questa funzione viene utilizzata con il PyTorch DataLoader per unire gli elementi del batch in modo che
        abbiano la stessa lunghezza, applicando il padding se necessario. I tensori vengono riempiti utilizzando
        il token di padding del tokenizer.

        Args:
            batch (list of tuples): Una lista di tuple, dove ogni tupla contiene due tensori 
                                    (input_ids_tensor e output_ids_tensor).

        Returns:
            tuple: Due tensori PyTorch con padding applicato:
                - input_ids_padded (torch.Tensor): I tensori degli input con padding.
                - output_ids_padded (torch.Tensor): I tensori degli output con padding.

        Raises:
            ValueError: Se tutti gli elementi del batch sono `None` o se non ci sono dati validi nel batch.
        """
        # Filtra gli item None
        batch = [(item[0], item[1]) for item in batch if item[0] is not None and item[1] is not None]
            
        if len(batch) == 0:
            raise ValueError("Tutti gli elementi del batch sono None.")
        # Verifica se input_ids e output_ids sono vuoti

        input_ids = [item[0] for item in batch]
        output_ids = [item[1] for item in batch]

        if not input_ids or not output_ids:
            raise ValueError("Nessun dato valido per il batch.")

        # Assicurati che siano tensori 1D
        #input_ids = [id.squeeze() if id.dim() > 1 else id for id in input_ids]
        #output_ids = [id.squeeze() if id.dim() > 1 else id for id in output_ids]

        # Usa pad_sequence con tensori 1D
        input_ids_padded = pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id)
        output_ids_padded = pad_sequence(output_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id)

        # Stampa le dimensioni dei tensori
        print(f"Collated Input IDs shape: {input_ids_padded.shape}, Collated Output IDs shape: {output_ids_padded.shape}")

        return input_ids_padded, output_ids_padded

    def update_dataset(self, new_data, output_file_path):
        """
        Aggiunge nuovi elementi al dataset e aggiorna il file JSON corrispondente.

        Questa funzione aggiorna sia i dati in memoria che il file su disco con nuovi esempi
        di descrizioni e codici. I nuovi dati vengono salvati in formato JSON.

        Args:
            new_data (dict): Nuovi dati da aggiungere al dataset, strutturati come un dizionario con chiavi di funzione e descrizioni/codici.
            output_file_path (str): Il percorso del file JSON in cui salvare il dataset aggiornato.
        """
        # Carica i dati esistenti se il file già esiste
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r', encoding='utf-8') as json_file:
                dataset = json.load(json_file)
        else:
            dataset = {}

        # Itera attraverso le chiavi e i valori nel dizionario
        dataset = [(func_info['docstring'],func_info['code'] ,func_info['description'], func_info['language']) for func_info in new_data.items()]
        self.inputs = [func_info['docstring'] for func_info in new_data.items()]
        self.outputs = [func_info['code'] for func_info in new_data.items()]
        self.item = [(func_info['description'], func_info['language']) for func_info in new_data.items()]

        # Salva il dataset aggiornato
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(dataset, json_file, ensure_ascii=False, indent=4)

        print(f"Dataset aggiornato con nuovi dati in {output_file_path}")