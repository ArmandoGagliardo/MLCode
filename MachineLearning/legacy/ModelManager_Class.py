from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification

class ModelManager:
    """
    Gestore del modello per caricare e gestire modelli di NLP pre-addestrati utilizzando la libreria Hugging Face.

    Questa classe supporta sia modelli per la generazione di testo (come CodeT5), sia modelli per la classificazione
    (come CodeBERT). Fornisce metodi per tokenizzare il testo, ottenere il modello e il tokenizer, e passare input
    attraverso il modello.

    Args:
        model_name (str): Nome o percorso del modello pre-addestrato da caricare (ad esempio, 'Salesforce/codet5-base').
        task_type (str): Tipo di task che il modello dovrà svolgere. Può essere:
            - 'generation' per la generazione di testo (ad esempio, CodeT5).
            - 'classification' per la classificazione di testo (ad esempio, CodeBERT).
            Default: 'generation'.
    
    Attributes:
        MAX_LENGTH (int): Lunghezza massima dei token per la tokenizzazione (impostata a 512).
        task_type (str): Tipo di task (generation o classification) definito durante l'inizializzazione.
        model_name (str): Il nome del modello pre-addestrato.
        tokenizer (PreTrainedTokenizer): Il tokenizer associato al modello.
        model (PreTrainedModel): Il modello pre-addestrato caricato, configurato per il tipo di task specificato.
    """
    def __init__(self, model_name, task_type):
        """
        Inizializza il gestore del modello.

        In base al tipo di task specificato, viene caricato un modello e un tokenizer pre-addestrato
        utilizzando la libreria Hugging Face Transformers. Se il task è 'generation', verrà caricato un modello
        di generazione sequenza-sequenza (es. CodeT5). Se il task è 'classification', verrà caricato un modello
        di classificazione (es. CodeBERT).

        Args:
            model_name (str): Nome o percorso del modello pre-addestrato.
            task_type (str): Tipo di task, 'generation' per modelli di generazione e 'classification' per modelli
                             di classificazione.
        
        Raises:
            ValueError: Se il tipo di task specificato non è supportato.
        """

        self.MAX_LENGTH = 32
        self.task_type = task_type
        self.model_name = model_name
        self.labels =["code","code_tokens","docstring","func_name","language","original_string"]

        # Carica il tokenizer in base al nome del modello
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)


        # Carica il modello in base al tipo di task
        if task_type == "generation":
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)  # Per CodeT5
        elif task_type == "classification":
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)  # Per CodeBERT
        else:
            raise ValueError(f"Unsupported task type {task_type}")
        
    def get_model(self):
        """
        Restituisce il modello caricato.

        Returns:
            PreTrainedModel: Il modello pre-addestrato caricato.
        """
        return self.model

    def get_tokenizer(self):
        """
        Restituisce il tokenizer caricato.

        Returns:
            PreTrainedTokenizer: Il tokenizer pre-addestrato caricato.
        """
        return self.tokenizer
    
    def tokenize(self, text):
        """
        Tokenizza il testo in base al modello selezionato.

        Utilizza il tokenizer pre-addestrato per convertire il testo in una sequenza di token, con padding e
        troncamento automatico. Il risultato viene restituito come tensore PyTorch.

        Args:
            text (str): Il testo da tokenizzare.

        Returns:
            torch.Tensor: I token del testo sotto forma di tensore PyTorch.
        """
        
        return self.tokenizer(text,return_tensors="pt",max_length=self.MAX_LENGTH, padding='max_length', truncation=True).input_ids[0]
    

    def forward(self, input_ids, attention_mask=None):
        """
        Passa gli input attraverso il modello e restituisce i risultati.

        In base al tipo di task, la funzione forward gestisce la generazione o la classificazione del testo.

        Args:
            input_ids (torch.Tensor): I token di input sotto forma di tensore.
            attention_mask (torch.Tensor, optional): La maschera di attenzione per indicare quali token devono
                                                     essere considerati durante il passaggio attraverso il modello.
        
        Returns:
            torch.Tensor: 
                - Se `task_type` è 'generation', restituisce la sequenza generata.
                - Se `task_type` è 'classification', restituisce i logits del modello.
        """
        if self.task_type == "generation":
            # Per modelli di generazione
            return self.model.generate(input_ids=input_ids, attention_mask=attention_mask)
        else:
            # Per modelli di classificazione
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
            return outputs.logits