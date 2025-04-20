# module/ui/app.py (Streamlit)
import streamlit as st
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
    result = pipeline.process(task_type, text)
    st.success(f"Risultato: {result}")