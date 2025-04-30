import re

def is_valid_code_sample(entry: dict) -> bool:
    name = entry.get("func_name", "").strip()
    output = entry.get("output", "").strip()
    prompt = entry.get("input", "").strip()

    # === 1. Validazione nome ===
    if not name or not name.isidentifier():
        return False
    if len(name) > 50 or any(c in name for c in "():{}[];"):
        return False
    if re.match(r"^[_a-zA-Z0-9]+\)$", name):  # nomi troncati tipo 'foo)'
        return False
    if name.lower() in {"is", "os", "f", "g", "h"}:
        return False

    # === 2. Output troppo corto o sospetto ===
    if len(output) < 20 or output.count("\n") < 1:
        return False
    if len(output) > 5000:
        return False
    if re.search(r"\b(pass|return None|throw new Exception|raise)\b", output) and output.count("\n") < 3:
        return False
    if output.strip().startswith("@") and not output.strip().startswith("@classmethod"):
        return False

    # === 3. Prompt coerente ===
    if not prompt or len(prompt.split()) < 3:
        return False
    if "con argomenti:" in prompt and prompt.strip().endswith(":"):
        return False
    if not re.search(r"Scrivi una funzione|Classe che|Metodo per", prompt, re.IGNORECASE):
        return False

    # === 4. Blacklist di pattern rotti ===
    blacklist = [
        "funzione chiamata '):", 
        "con argomenti: ):", 
        "funzione python chiamata '   '", 
        "def __", 
        "return", 
        "):\n", 
        "self,",
        "}\n"
    ]
    for b in blacklist:
        if b in name or b in prompt:
            return False

    # === 5. Semantica basilare ===
    if re.search(r"def\s+[a-zA-Z_]", output) or re.search(r"(public|static|class|function)\s", output):
        return True
    if "{" in output and "}" in output and output.count(";") >= 2:
        return True
    if output.count("return") >= 1:
        return True

    return False