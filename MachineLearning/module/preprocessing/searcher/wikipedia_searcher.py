# 📂 module/preprocessing/wikipedia_searcher.py
import wikipedia

class WikipediaSearcher:
    def __init__(self):
        wikipedia.set_lang("it")  # Imposta la lingua italiana

    def search(self, keywords: str):
        try:
            page = wikipedia.page(keywords)
            print( f" Content Wikipedia per {keywords}: {page.content[:100]}...")  # Stampa i primi 100 caratteri
            return [page.content]  # Restituisce una lista con il contenuto
        except Exception as e:
            print(f"❌ Errore Wikipedia per {keywords}: {e}")
            return []
