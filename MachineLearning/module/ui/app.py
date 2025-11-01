# module/ui/app.py (Streamlit)
import streamlit as st
import sys
from pathlib import Path

# Aggiunge la root del progetto al PYTHONPATH
BASE_PATH = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_PATH))

# Importa le classi necessarie
from module.model.model_manager import ModelManager

# Configurazione della pagina
st.set_page_config(
    page_title="AI Code Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile CSS personalizzato
st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .stTextArea textarea {
            font-family: 'Courier New', Courier, monospace;
        }
    </style>
""", unsafe_allow_html=True)

# Titolo principale
st.title("🤖 AI Code Assistant")

# Sidebar per le opzioni
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    # Selezione del modello
    model_type = st.selectbox(
        "Seleziona il tipo di task",
        ["text_classification", "code_generation", "security_classification"],
        help="Scegli il tipo di analisi da eseguire sul codice"
    )
    
    # Mostra informazioni sul modello
    st.info(f"""
        📌 Modello selezionato: {model_type}
        
        Questo modello è ottimizzato per:
        - {'Classificazione del testo' if 'text' in model_type else 'Generazione di codice' if 'code' in model_type else 'Analisi di sicurezza'}
        - Input size: max 512 tokens
        """)
    
    # Impostazioni avanzate
    with st.expander("🔧 Impostazioni avanzate"):
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            help="Controlla la creatività del modello"
        )

# Area principale per l'input
st.header("📝 Input")
code_input = st.text_area(
    "Inserisci il codice o il testo da analizzare",
    height=200,
    help="Incolla qui il codice o il testo che vuoi analizzare"
)

# Area dei risultati
if st.button("🚀 Analizza", type="primary"):
    if code_input.strip():
        try:
            with st.spinner("🔄 Elaborazione in corso..."):
                # Inizializza il model manager
                model_manager = ModelManager(
                    task=model_type,
                    model_name="microsoft/codebert-base"
                )
                
                # Ottiene il modello
                model = model_manager.get_model()
                
                # Tokenizza l'input
                inputs = model_manager.tokenizer(
                    code_input,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                ).to(model_manager.device)
                
                # Esegue l'inferenza
                outputs = model(**inputs)
                
                # Processa i risultati in base al task
                if "classification" in model_type:
                    logits = outputs.logits
                    predictions = logits.argmax(-1)
                    confidence = logits.softmax(-1).max().item()
                    
                    # Mostra i risultati
                    st.success(f"✅ Analisi completata!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Classificazione",
                            f"Classe {predictions.item()}"
                        )
                    with col2:
                        st.metric(
                            "Confidenza",
                            f"{confidence:.2%}"
                        )
                else:
                    # Per generazione di codice
                    generated = model_manager.tokenizer.decode(
                        outputs.logits.argmax(-1)[0],
                        skip_special_tokens=True
                    )
                    
                    st.success("✅ Codice generato con successo!")
                    st.code(generated, language="python")
                
        except Exception as e:
            st.error(f"❌ Si è verificato un errore: {str(e)}")
            st.exception(e)
    else:
        st.warning("⚠️ Inserisci del testo prima di procedere")

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using PyTorch & Transformers"
)