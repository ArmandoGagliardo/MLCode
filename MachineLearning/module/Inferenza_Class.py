from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class Inferenza_Class():
    """
    Classe per eseguire inferenze con un modello Seq2Seq addestrato.

    Questa classe gestisce il caricamento del modello e del tokenizer e fornisce un metodo per generare risposte
    a partire da un input di testo.

    Args:
        model_save_path (str): Il percorso al modello salvato da cui eseguire inferenze.
    
    Attributes:
        model (PreTrainedModel): Modello Seq2Seq caricato da Hugging Face Transformers.
        tokenizer (PreTrainedTokenizer): Tokenizer associato al modello per la tokenizzazione del testo di input.
    """
    def __init__(self,model_save_path):

        """
        Inizializza l'oggetto Inferenza_Class caricando il modello e il tokenizer dal percorso specificato.

        Args:
            model_save_path (str): Percorso al modello salvato.
        
        Raises:
            Exception: Se il modello o il tokenizer non possono essere caricati.
        """

        try:
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_save_path)
            self.tokenizer = AutoTokenizer.from_pretrained(model_save_path)
        except Exception as e:
            raise RuntimeError(f"❌ Errore nel caricamento del modello generazione: {e}")


    def generate_response(self,input_text,max_new_tokens=128,temperature=0.8):
        """
        Genera una risposta basata su un input di testo utilizzando il modello Seq2Seq.

        Args:
            input_text (str): Testo di input su cui generare la risposta.
            max_new_tokens (int): Numero massimo di token da generare.
            temperature (float): Parametro di temperatura per la generazione (controlla la casualità).

        Returns:
            str: Testo generato come output del modello.
        """
        # Tokenizza l'input
        inputs = self.tokenizer(input_text, return_tensors="pt")  # Restituisce i tensori per PyTorch
        # Genera l'output
        outputs = self.model.generate(**inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=50,  # Limita le scelte
        top_p=0.95,  # Usando nucleus sampling
        do_sample= True,
        num_beams=5,
        early_stopping=True
        )
        # Decodifica l'output in un formato leggibile
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
