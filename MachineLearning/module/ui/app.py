# module/ui/app.py (Streamlit)
import streamlit as st
import sys
from pathlib import Path
# Aggiunge la root del progetto al PYTHONPATH
BASE_PATH = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_PATH))

from module.tasks.task_pipeline import TaskPipeline

st.title("💡 AI Assistant Universale")

text = st.text_area("Inserisci codice, comando o descrizione")
task_type = st.selectbox("Task da eseguire", ["text_classification", "code_generation", "security_classification", "code_explanation"])

model_paths = {
    "code_generation": "models/code_generation",
    "text_classification": "models/text_classification",
    "security_classification": "models/security_classification"
}

if st.button("Esegui"):
    pipeline = TaskPipeline(model_paths)
    result = pipeline.process(text)
    st.success(f"Risultato: {result}")