# 📁 module/tasks/task_identifier.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class TaskIdentifier:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Esempi di riferimento per ogni tipo di task
        self.task_prompts = {
            "code_generation": [
                "Scrivi una funzione Python che somma due numeri",
                "Genera codice per ordinare una lista",
                "Crea una funzione che calcoli il fattoriale"
            ],
            "code_explanation": [
                "Spiega cosa fa questo codice",
                "Descrivi il significato del seguente snippet Python"
            ],
            "security_classification": [
                "Questo codice è sicuro?",
                "Il codice contiene vulnerabilità?",
                "Il codice è soggetto ad attacchi injection?"
            ]
        }

        # Precalcolo gli embedding medi per ogni task
        self.task_embeddings = {
            task: np.mean(self.model.encode(prompts), axis=0)
            for task, prompts in self.task_prompts.items()
        }

    def identify(self, prompt: str) -> str:
        input_embedding = self.model.encode([prompt])[0]

        best_task = None
        best_score = -1

        for task, task_emb in self.task_embeddings.items():
            score = cosine_similarity(
                [input_embedding],
                [task_emb]
            )[0][0]

            if score > best_score:
                best_score = score
                best_task = task

        return best_task
