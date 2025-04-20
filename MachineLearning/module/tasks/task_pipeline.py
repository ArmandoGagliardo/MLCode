# module/tasks/task_pipeline.py (completo)
from module.tasks.text_classifier import TextClassifier
from module.tasks.inference_engine import InferenceEngine
from module.tasks.security_classifier import SecurityClassifier

class TaskPipeline:
    def __init__(self, model_paths: dict):
        self.classifier = TextClassifier(model_paths["text_classification"])
        self.generator = InferenceEngine(model_paths["code_generation"])
        self.security = SecurityClassifier(model_paths["security_classification"])

    def process(self, task_type: str, text: str):
        if task_type == "text_classification":
            result = self.classifier.classify(text)
            return "code" if result == 1 else "text"

        elif task_type == "code_generation":
            return self.safe_generate(text)

        elif task_type == "security_classification":
            return self.security.classify(text)

        elif task_type == "code_explanation":
            return self.explain_code(text)

        else:
            return "[❌ Task non supportato]"

    def safe_generate(self, text: str) -> str:
        result = self.generator.generate(text)
        if not result.strip() or len(result.strip()) < 10:
            return "[⚠️ Risposta generata troppo corta o vaga]"
        return result

    def explain_code(self, code: str, language: str = "Python") -> str:
        prompt = f"Spiega cosa fa questo codice {language}:\n{code}"
        return self.safe_generate(prompt)

    def debug_test(self, input_text: str):
        task_type = self.process("text_classification", input_text)
        print(f"[🧠 Tipo rilevato: {task_type}]")

        if task_type == "text":
            result = self.process("code_generation", input_text)
            print(f"[💡 Codice generato]:\n{result}")
        else:
            result = self.process("security_classification", input_text)
            print(f"[🔒 Sicurezza]:\n{result}")
