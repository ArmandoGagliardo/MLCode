# 📂 module/text/text_quality.py
import re
from langdetect import detect


def is_valid_text(text: str) -> bool:
    # Lunghezza minima
    if len(text.strip().split()) < 10:
        return False

    # Caratteri alfabetici sufficienti
    if len(re.findall(r"[A-Za-zÀ-ÿ]", text)) < 20:
        return False

    # Controllo lingua (opzionale: "it" o "en")
    try:
        lang = detect(text)
        if lang not in {"it", "en"}:
            return False
    except:
        return False

    return True
