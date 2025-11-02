"""
Esempio Training - Addestra un modello con i dati estratti

Questo script mostra come utilizzare le funzioni estratte per addestrare
un modello di machine learning per code generation.

Requisiti:
- Dati estratti in datasets/local_backup/code_generation/
- PyTorch e Transformers installati
- GPU consigliata (ma funziona anche con CPU)

Uso:
    python example_training.py
    
    # Con opzioni custom
    python example_training.py --epochs 10 --batch-size 8
"""

import json
import torch
from pathlib import Path
from datetime import datetime
import argparse


def check_pytorch():
    """Verifica disponibilità PyTorch e GPU"""
    print("🔍 Verifica ambiente di training...")
    print()
    
    try:
        import torch
        print(f"✅ PyTorch versione: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ GPU disponibile: {torch.cuda.get_device_name(0)}")
            print(f"   Memoria GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            device = "cuda"
        else:
            print("⚠️  GPU non disponibile - training su CPU (più lento)")
            device = "cpu"
        
        print(f"📍 Device di training: {device}")
        print()
        return device
        
    except ImportError:
        print("❌ PyTorch non installato!")
        print()
        print("Installa con:")
        print("   pip install torch transformers datasets")
        return None


def check_transformers():
    """Verifica Transformers"""
    try:
        import transformers
        print(f"✅ Transformers versione: {transformers.__version__}")
        print()
        return True
    except ImportError:
        print("❌ Transformers non installato!")
        print("   pip install transformers datasets")
        return False


def load_training_data(data_dir: Path):
    """Carica tutti i dati JSON per il training"""
    print(f"📂 Caricamento dati da: {data_dir}")
    
    all_data = []
    json_files = list(data_dir.glob("*.json"))
    
    # Escludi file di analisi
    json_files = [f for f in json_files if f.name != "analysis_summary.json"]
    
    if not json_files:
        print(f"⚠️  Nessun file JSON trovato in {data_dir}")
        print()
        print("Esegui prima:")
        print("   python example_single_repo.py")
        print("   oppure")
        print("   python example_bulk_processing.py")
        return None
    
    print(f"📊 Trovati {len(json_files)} file da caricare")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
        except Exception as e:
            print(f"⚠️  Errore leggendo {json_file.name}: {e}")
    
    print(f"✅ Caricati {len(all_data)} esempi totali")
    print()
    
    return all_data


def prepare_dataset(data):
    """Prepara dataset per training"""
    print("🔧 Preparazione dataset...")
    
    # Filtra esempi validi
    valid_data = [
        d for d in data
        if d.get('input') and d.get('output') and len(d.get('output', '')) >= 10
    ]
    
    print(f"   Esempi validi: {len(valid_data)}/{len(data)}")
    
    # Statistiche per linguaggio
    from collections import Counter
    lang_counts = Counter(d.get('language', 'unknown') for d in valid_data)
    
    print(f"   Breakdown per linguaggio:")
    for lang, count in lang_counts.most_common():
        percentage = count / len(valid_data) * 100
        print(f"      {lang:12s}: {count:5d} ({percentage:5.1f}%)")
    
    print()
    return valid_data


def split_dataset(data, train_ratio=0.8):
    """Split train/validation"""
    print(f"📊 Split dataset (train: {train_ratio*100:.0f}%, val: {(1-train_ratio)*100:.0f}%)...")
    
    import random
    random.shuffle(data)
    
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    
    print(f"   Training: {len(train_data)} esempi")
    print(f"   Validation: {len(val_data)} esempi")
    print()
    
    return train_data, val_data


def train_model_simple(train_data, val_data, device, epochs=3, batch_size=4):
    """
    Training semplificato per dimostrazione
    
    Nota: Questo è un esempio base. Per training reale usa:
    - module/model/train_generic.py
    - oppure segui GUIDA_TRAINING.md
    """
    print("=" * 70)
    print("🚀 INIZIO TRAINING (Versione Demo)")
    print("=" * 70)
    print()
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from torch.utils.data import Dataset, DataLoader
        import torch.nn as nn
        
        # Modello piccolo per demo (350M parametri)
        model_name = "Salesforce/codegen-350M-mono"
        
        print(f"📦 Caricamento modello: {model_name}")
        print("   (Primo download può richiedere tempo...)")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        model.to(device)
        
        print("✅ Modello caricato!")
        print()
        
        # Dataset custom
        class CodeDataset(Dataset):
            def __init__(self, data, tokenizer, max_length=256):
                self.data = data
                self.tokenizer = tokenizer
                self.max_length = max_length
            
            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, idx):
                item = self.data[idx]
                
                # Combina input e output per training causal LM
                text = f"# Task: {item['input']}\n{item['output']}"
                
                encoding = self.tokenizer(
                    text,
                    max_length=self.max_length,
                    padding='max_length',
                    truncation=True,
                    return_tensors='pt'
                )
                
                return {
                    'input_ids': encoding['input_ids'].squeeze(),
                    'attention_mask': encoding['attention_mask'].squeeze(),
                    'labels': encoding['input_ids'].squeeze()
                }
        
        # Crea datasets
        train_dataset = CodeDataset(train_data, tokenizer)
        val_dataset = CodeDataset(val_data, tokenizer)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Optimizer
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
        
        print(f"⚙️  Configurazione:")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Learning rate: 5e-5")
        print(f"   Total batches/epoch: {len(train_loader)}")
        print()
        
        # Training loop
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            print("-" * 70)
            print(f"📚 Epoch {epoch + 1}/{epochs}")
            print("-" * 70)
            
            # Training
            model.train()
            train_loss = 0
            
            for batch_idx, batch in enumerate(train_loader):
                # Move to device
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                # Forward pass
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                
                # Progress ogni 10 batch
                if (batch_idx + 1) % 10 == 0:
                    avg_loss = train_loss / (batch_idx + 1)
                    progress = (batch_idx + 1) / len(train_loader) * 100
                    print(f"   Batch {batch_idx + 1}/{len(train_loader)} ({progress:.1f}%) - Loss: {avg_loss:.4f}")
            
            avg_train_loss = train_loss / len(train_loader)
            
            # Validation
            model.eval()
            val_loss = 0
            
            with torch.no_grad():
                for batch in val_loader:
                    input_ids = batch['input_ids'].to(device)
                    attention_mask = batch['attention_mask'].to(device)
                    labels = batch['labels'].to(device)
                    
                    outputs = model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    
                    val_loss += outputs.loss.item()
            
            avg_val_loss = val_loss / len(val_loader)
            
            print()
            print(f"📊 Risultati Epoch {epoch + 1}:")
            print(f"   Train Loss: {avg_train_loss:.4f}")
            print(f"   Val Loss: {avg_val_loss:.4f}")
            
            # Salva best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                print(f"   💾 Nuovo miglior modello! (Val Loss: {best_val_loss:.4f})")
                
                # Salva modello
                output_dir = Path("models/demo_trained")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                model.save_pretrained(output_dir)
                tokenizer.save_pretrained(output_dir)
                
                print(f"   ✅ Salvato in: {output_dir}")
            
            print()
        
        print("=" * 70)
        print("🎉 TRAINING COMPLETATO!")
        print("=" * 70)
        print()
        print(f"📊 Risultati Finali:")
        print(f"   Best Validation Loss: {best_val_loss:.4f}")
        print(f"   Modello salvato in: models/demo_trained/")
        print()
        
        # Test inference
        print("-" * 70)
        print("🧪 Test Inference")
        print("-" * 70)
        
        test_prompt = "# Task: Write a python function named calculate_sum\n"
        inputs = tokenizer(test_prompt, return_tensors='pt').to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Prompt: {test_prompt}")
        print(f"Generated:\n{generated}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante training: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Training Example")
    parser.add_argument('--epochs', type=int, default=3, help='Numero di epoch')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--data-dir', type=str, default='datasets/local_backup/code_generation',
                       help='Directory con i dati')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 EXAMPLE TRAINING - CODE GENERATION MODEL")
    print("=" * 70)
    print()
    
    # 1. Verifica ambiente
    device = check_pytorch()
    if device is None:
        return
    
    if not check_transformers():
        return
    
    # 2. Carica dati
    data_dir = Path(args.data_dir)
    data = load_training_data(data_dir)
    
    if data is None or len(data) == 0:
        return
    
    # 3. Prepara dataset
    data = prepare_dataset(data)
    
    if len(data) < 100:
        print("⚠️  Hai meno di 100 esempi. Risultati potrebbero essere limitati.")
        print("   Considera raccogliere più dati con example_bulk_processing.py")
        print()
    
    # 4. Split train/val
    train_data, val_data = split_dataset(data)
    
    # 5. Training
    print("💡 NOTA: Questo è un training DEMO semplificato")
    print("   Per training production usa: python main.py --train code_generation")
    print("   Vedi GUIDA_TRAINING.md per dettagli completi")
    print()
    
    response = input("Continuare con training demo? (y/n): ")
    if response.lower() != 'y':
        print("Training annullato.")
        return
    
    print()
    
    success = train_model_simple(
        train_data,
        val_data,
        device,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    if success:
        print("=" * 70)
        print("✅ ESEMPIO COMPLETATO CON SUCCESSO!")
        print("=" * 70)
        print()
        print("📚 Prossimi Passi:")
        print("   1. Vedi GUIDA_TRAINING.md per training production")
        print("   2. Usa python main.py --train code_generation per training completo")
        print("   3. Deploy su GPU con deploy_to_gpu.sh")
        print()


if __name__ == "__main__":
    main()
