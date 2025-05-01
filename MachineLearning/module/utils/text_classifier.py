import re
import string
import unicodedata
from collections import defaultdict
from urllib.parse import urlparse

class TextClassifier:
    def __init__(self):
        self.labels = {
            "medical": "articolo sanitario o medico",
            "legal": "notizia giudiziaria o legale",
            "finance": "contenuto economico-finanziario",
            "sports": "notizia sportiva",
            "culture": "contenuto culturale (arte, cinema, letteratura)",
            "crime": "cronaca nera",
            "world": "notizia geopolitica o estera",
            "news": "notizia generica",
            "history": "testo storico",
            "science": "contenuto scientifico",
            "grammar": "contenuto di grammatica",
            "literature": "contenuto letterario",
            "religion": "tema religioso",
            "education": "testo educativo o scolastico",
            "philosophy": "testo filosofico",
            "fantasy": "narrazione fantasy o immaginaria",
            "tech": "argomento tecnologico",
            "mythology": "contenuto mitologico",
            "nature": "testo sulla natura",
            "narrative": "narrazione o monologo",
            "book": "tratto da un libro"
        }

        # regex semantiche ed euristiche
        self.blacklist_keywords = {
            "medical": ["medic", "ospedale", "salute", "clinica", "terapia", "farmaco", "paziente"],
            "legal": ["giudice", "tribunale", "sentenza", "processo", "reato", "penale", "codice"],
            "finance": ["borsa", "azioni", "investimenti", "mercati", "spread", "banche"],
            "crime": ["omicidio", "rapina", "furto", "arrestato", "carcere", "aggressione"],
            "sports": ["calcio", "partita", "gol", "tennis", "olimpiadi", "campionato"],
            "culture": ["arte", "film", "cinema", "mostra", "libro", "romanzo", "teatro"],
            "world": ["nazioni unite", "estero", "confine", "guerra", "ucraina", "nato"],
            "science": ["scienza", "ricerca", "dati", "esperimento", "laboratorio", "fisica"],
            "grammar": ["verbo", "sintassi", "grammatica", "aggettivo", "analisi logica"],
            "literature": ["poesia", "narrativa", "racconto", "manzoni", "leopardi", "letteratura"],
            "religion": ["dio", "chiesa", "cristianesimo", "religione", "papa", "vangelo"],
            "education": ["lezione", "studente", "insegnante", "compito", "esame", "scuola"],
            "philosophy": ["etica", "filosofia", "platon", "kant", "hegel", "socrate"],
            "fantasy": ["drago", "magia", "castello", "elfo", "reame", "sortilegio"],
            "tech": ["algoritmo", "intelligenza artificiale", "software", "python", "machine learning"],
            "mythology": ["zeus", "dea", "olimpo", "mitologia", "poseidone", "titani"],
            "nature": ["ambiente", "clima", "ecosistema", "foresta", "animali", "biodiversit"],
            "narrative": ["disse", "raccontava", "pensava", "camminava", "guardava"],
            "book": ["capitolo", "romanzo", "autore", "prefazione", "introduzione"]
        }

        self.url_patterns = {
            "finance": ["/borsa/", "/economia/", "/finanza/"],
            "medical": ["/salute/", "/sanita/"],
            "legal": ["/giustizia/", "/cronaca-giudiziaria/"],
            "sports": ["/sport/"],
            "culture": ["/cultura/", "/arte/", "/cinema/"]
        }

    def normalize_text(self, text):
        text = unicodedata.normalize("NFKD", text.lower())
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    def classify(self, text, url=None, title=""):
        scores = defaultdict(int)
        normalized = self.normalize_text(text + " " + title)

        for label, keywords in self.blacklist_keywords.items():
            for kw in keywords:
                if kw in normalized:
                    scores[label] += 1

        if url:
            domain_path = urlparse(url).path.lower()
            for label, patterns in self.url_patterns.items():
                for p in patterns:
                    if p in domain_path:
                        scores[label] += 2  # URL match pesa di più

        if not scores:
            if len(text.split()) < 10:
                return "short"
            elif len(text.split()) > 200:
                return "article"
            else:
                return "statement"

        # ritorna la categoria con score massimo
        best_label = max(scores, key=scores.get)
        return best_label

    def explain(self, text, url=None, title=""):
        label = self.classify(text, url, title)
        return self.labels.get(label, "contenuto generico")


# Esempio di utilizzo:
if __name__ == "__main__":
    classifier = TextClassifier()
    text = "Il paziente è stato trasferito in terapia intensiva presso l'ospedale San Raffaele."
    print("Categoria:", classifier.classify(text))
    print("Descrizione:", classifier.explain(text))
