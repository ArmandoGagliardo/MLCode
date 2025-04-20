import json
import os

# Percorso dove salvare il dataset
OUTPUT_DIR = os.path.join(os.getcwd(), "dataset")
os.makedirs(OUTPUT_DIR, exist_ok=True)
DATASET_FILE = os.path.join(OUTPUT_DIR, "dataset_classification.json")

# Esempi bilanciati
examples = [
    # TESTO (label: 0)
    "Scrivi una funzione Python che restituisca la somma di due numeri.",
    "Genera una lista di numeri primi.",
    "Determina se un numero è pari.",
    "Rimuovi duplicati da una lista.",
    "Ordina una lista in ordine decrescente.",
    "Conta le occorrenze di un valore.",
    "Unisci due dizionari.",
    "Calcola la media di una lista di numeri.",
    "Verifica se una parola è palindroma.",
    "Inverti una stringa.",

    # CODICE (label: 1)
    "def sum(a, b): return a + b",
    "def primes(n): return [p for p in range(2,n) if all(p%d!=0 for d in range(2,p))]",
    "def is_even(n): return n % 2 == 0",
    "def remove_duplicates(lst): return list(set(lst))",
    "def sort_desc(lst): return sorted(lst, reverse=True)",
    "def count_occurrences(lst, val): return lst.count(val)",
    "def merge(d1, d2): return {**d1, **d2}",
    "def average(lst): return sum(lst) / len(lst)",
    "def is_palindrome(s): return s == s[::-1]",
    "def reverse(s): return s[::-1]",
]

# Associa le label: 0 per testo, 1 per codice
dataset = [
    {"text": text, "label": 0 if i < 10 else 1}
    for i, text in enumerate(examples)
]

# Salva in JSON
with open(DATASET_FILE, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print(f"✅ Dataset classificazione salvato in: {DATASET_FILE}")
