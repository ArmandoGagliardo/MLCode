"""
Esempio Uso Modello Addestrato - Inferenza e Code Generation

Questo script mostra come utilizzare un modello addestrato per generare codice.

Requisiti:
- Modello addestrato in models/demo_trained/ o models/saved/
- PyTorch e Transformers installati

Uso:
    python example_use_trained_model.py
    
    # Con modello custom
    python example_use_trained_model.py --model models/saved/code_generation_best
"""

import argparse
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM


def load_model(model_path: str):
    """Carica modello e tokenizer"""
    print(f"📦 Caricamento modello da: {model_path}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        
        # Move to GPU se disponibile
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()  # Modalità evaluation
        
        print(f"✅ Modello caricato su: {device}")
        print()
        
        return model, tokenizer, device
    
    except Exception as e:
        print(f"❌ Errore caricamento modello: {e}")
        print()
        print("Verifica che esista un modello addestrato:")
        print("   python example_training.py  # Per addestrare")
        print("   oppure")
        print("   python main.py --train code_generation")
        return None, None, None


def generate_code(model, tokenizer, device, prompt: str, max_length=150, temperature=0.7, num_return=1):
    """
    Genera codice dal prompt
    
    Args:
        model: Modello addestrato
        tokenizer: Tokenizer
        device: Device (cuda/cpu)
        prompt: Prompt di input
        max_length: Lunghezza massima output
        temperature: Controllo creatività (0.1=deterministico, 1.0=creativo)
        num_return: Numero di varianti da generare
    """
    # Prepara input
    inputs = tokenizer(prompt, return_tensors='pt').to(device)
    
    # Genera
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=num_return,
            temperature=temperature,
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode outputs
    results = []
    for output in outputs:
        generated = tokenizer.decode(output, skip_special_tokens=True)
        results.append(generated)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Use trained model for code generation")
    parser.add_argument('--model', type=str, default='models/demo_trained',
                       help='Path to trained model')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 CODE GENERATION - USO MODELLO ADDESTRATO")
    print("=" * 70)
    print()
    
    # Carica modello
    model_path = Path(args.model)
    
    if not model_path.exists():
        print(f"⚠️  Modello non trovato: {model_path}")
        print()
        print("Opzioni disponibili:")
        
        # Cerca modelli esistenti
        possible_paths = [
            Path("models/demo_trained"),
            Path("models/saved/code_generation_best"),
            Path("models/saved/code_generation"),
        ]
        
        found_models = [p for p in possible_paths if p.exists()]
        
        if found_models:
            print("Modelli trovati:")
            for p in found_models:
                print(f"   - {p}")
            print()
            print(f"Usa: python {__file__} --model {found_models[0]}")
        else:
            print("Nessun modello trovato. Addestra prima:")
            print("   python example_training.py")
        
        return
    
    model, tokenizer, device = load_model(str(model_path))
    
    if model is None:
        return
    
    # Modalità interattiva
    if args.interactive:
        print("=" * 70)
        print("💬 MODALITÀ INTERATTIVA")
        print("=" * 70)
        print("Inserisci i tuoi prompt. Digita 'exit' per uscire.")
        print()
        
        while True:
            try:
                prompt = input("🔹 Prompt: ").strip()
                
                if prompt.lower() in ['exit', 'quit', 'q']:
                    print("👋 Arrivederci!")
                    break
                
                if not prompt:
                    continue
                
                print()
                print("🤖 Generazione in corso...")
                
                # Aggiungi formato se non presente
                if not prompt.startswith("#"):
                    prompt = f"# Task: {prompt}\n"
                
                results = generate_code(model, tokenizer, device, prompt, max_length=200)
                
                print()
                print("📝 Generated Code:")
                print("-" * 70)
                print(results[0])
                print("-" * 70)
                print()
            
            except KeyboardInterrupt:
                print()
                print("👋 Interruzione utente. Arrivederci!")
                break
            except Exception as e:
                print(f"❌ Errore: {e}")
                print()
    
    else:
        # Modalità demo con esempi pre-definiti
        print("=" * 70)
        print("🧪 DEMO MODE - ESEMPI PREDEFINITI")
        print("=" * 70)
        print()
        
        examples = [
            {
                "language": "Python",
                "prompt": "# Task: Write a python function named calculate_factorial\n",
                "description": "Calcolo fattoriale"
            },
            {
                "language": "JavaScript",
                "prompt": "# Task: Write a javascript async function named fetchData\n",
                "description": "Fetch asincrono"
            },
            {
                "language": "Python",
                "prompt": "# Task: Write a python function named binary_search\n",
                "description": "Ricerca binaria"
            },
            {
                "language": "Go",
                "prompt": "# Task: Write a go function named handleRequest\n",
                "description": "HTTP handler"
            },
            {
                "language": "Rust",
                "prompt": "# Task: Write a rust function named parse_config\n",
                "description": "Config parser"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"Esempio {i}/{len(examples)}: {example['description']} ({example['language']})")
            print("-" * 70)
            
            print(f"📥 Prompt:")
            print(f"   {example['prompt'].strip()}")
            print()
            
            print("🤖 Generazione...")
            results = generate_code(
                model, 
                tokenizer, 
                device, 
                example['prompt'],
                max_length=150,
                temperature=0.7
            )
            
            print()
            print("📝 Generated Code:")
            print(results[0])
            print()
            
            if i < len(examples):
                input("Premi ENTER per esempio successivo...")
                print()
        
        print("=" * 70)
        print("✅ DEMO COMPLETATA")
        print("=" * 70)
        print()
        print("💡 Usa --interactive per modalità interattiva:")
        print(f"   python {__file__} --interactive")
        print()


def test_variations():
    """Test con diverse temperature e parametri"""
    print("=" * 70)
    print("🔬 TEST VARIAZIONI - PARAMETRI GENERATION")
    print("=" * 70)
    print()
    
    model_path = "models/demo_trained"
    model, tokenizer, device = load_model(model_path)
    
    if model is None:
        return
    
    prompt = "# Task: Write a python function named sort_list\n"
    
    print(f"Prompt: {prompt}")
    print()
    
    # Test diverse temperature
    temperatures = [0.3, 0.7, 1.0]
    
    for temp in temperatures:
        print(f"🌡️  Temperature: {temp}")
        print("-" * 70)
        
        results = generate_code(
            model, 
            tokenizer, 
            device, 
            prompt,
            max_length=100,
            temperature=temp,
            num_return=1
        )
        
        print(results[0])
        print()
    
    print("=" * 70)
    print("📊 Osservazioni:")
    print("   - Temperature bassa (0.3): Più deterministico, sicuro")
    print("   - Temperature media (0.7): Bilanciato")
    print("   - Temperature alta (1.0): Più creativo, variato")
    print("=" * 70)


if __name__ == "__main__":
    main()
    
    # Decomment per test variazioni
    # test_variations()
