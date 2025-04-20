from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class InferenceEngine:
    '''
    Motore di inferenza per generazione codice.
    Estende la generazione con sampling, top-p e temperature per evitare risposte corte o generiche.
    '''
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    def generate(self, prompt: str):
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        
        output = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_new_tokens=128,
            do_sample=True,           # Sampling attivo
            top_p=0.95,               # Nucleus sampling
            temperature=0.8,          # Decisivo per controllare la creatività
            num_return_sequences=1,
            early_stopping=True,
            num_beams=5           # Beam search per migliorare la qualità
        )
        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
        return decoded
