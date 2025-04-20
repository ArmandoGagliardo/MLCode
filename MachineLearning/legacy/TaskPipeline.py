from ClassificationModel_Class import ClassificationModel_Class
from module.Inferenza_Class import Inferenza_Class
import ast

class TaskPipeline_Class:
    def __init__(self, path_model_generation, path_model_classification):
        """
        Inizializza la pipeline con entrambi i modelli (classificazione + generazione).
        """
        self.classifier = ClassificationModel_Class(path_model_classification)
        self.generator = Inferenza_Class(path_model_generation)

    def is_code_like(self, text):
        """
        Metodo di backup per capire se un input assomiglia a codice Python.
        """
        try:
            ast.parse(text)
            return True
        except:
            return False

    def process_input(self, input_text):
        """
        Gestisce l'input: classifica se è codice o testo, e agisce di conseguenza.
        """
        input_type = self.classifier.classify(input_text)

        # Fallback in caso di incertezza del classificatore
        if input_type not in ["code", "text"]:
            input_type = "code" if self.is_code_like(input_text) else "text"

        if input_type == "code":
            print("✅ Input classificato come codice.")
            prompt = f"Spiega cosa fa questo codice Python:\n{input_text}"
        else:
            print("✅ Input classificato come testo.")
            prompt = f"Scrivi una funzione Python che {input_text.lower().strip()}"

        result = self.generator.generate_response(prompt)

        # Filtro: se la risposta è troppo corta, fallback
        if len(result.strip().split()) < 3:
            return "[⚠️ Risposta generata troppo corta o vaga]"
        return result
