import time
import random
import hashlib
import json,re,unicodedata
from bs4 import BeautifulSoup
from pathlib import Path
from module.preprocessing.cleaning.text_cleaner import TextCleaner
from transformers import AutoTokenizer
from urllib.parse import urlparse
from module.utils.stealth_crawler import StealthCrawler
from module.scripts.duplicate_manager import DuplicateManager

def _generic_html_parser(soup: BeautifulSoup) -> dict:
    title = soup.title.string.strip() if soup.title else "UNKNOWN"
    elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "div"])
    return {"title": title, "text": elements}
# Mappa dominio → funzione parser
SITE_PARSERS = {
    "ansa.it": _generic_html_parser,
    # puoi aggiungere altri: "repubblica.it": parse_repubblica
}


class WebTextCrawler:
    def __init__(self, searcher, max_pages=50, min_characters=80):
        self.searcher = searcher
        self.max_pages = max_pages
        self.DATA_DIR = Path("data/dataset_italiano")
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.CLEANED_DIR = self.DATA_DIR / "cleaned"
        self.METADATA_PATH = self.DATA_DIR / "metadata.jsonl"
        self.MIN_CHARACTERS = min_characters
        self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-italian-cased")
        self._setup_folders()
        self._validate_state()
        self.text_cleaner = TextCleaner()


    def crawl(self, keywords: list[str]):
        
        for keyword in keywords:

            pages_downloaded = 0  # Limite di pagine scaricate per keyword

            print(f"🔍 Inizio ricerca per: {keyword}")
            try:
                items = self.searcher.search(keyword)
            except Exception as e:
                print(f"❌ Errore nella ricerca: {e}")
                continue

            for item in items:

                if pages_downloaded >= self.max_pages:
                    print("📦 Limite di pagine scaricate raggiunto.")
                    break

                try:
                    # Decide: link o testo diretto ## isinstance(item, str) and 
                    if item.startswith("http") or item.startswith("https"):
                        print(f"🌐 Scarico pagina -- ")
                        content, title,_ = self._download_page(item)
                        if not content:
                            print(f"⚠️ Link obsoleto {item}, salto.")
                            continue
                    else:
                        print(f"📄 Uso testo diretto da ricerca.")
                        content = item

                    filename_base = self._hash_string(content)
                    if not content:
                        print(f"⚠️ Contenuto vuoto, salto.")
                        continue
                    if len(content.strip()) < self.MIN_CHARACTERS and len(content.strip()) > 5:
                        print(f"⚠️ Contenuto corto ({len(content.strip())} caratteri), ma salvo comunque con tag [SHORT].")
                        content = f"[SHORT]\n{content}"


                    # Salva file RAW
                    raw_path = self._save_raw_text(filename_base, content)
                    
                    if not raw_path:
                        print(f"⚠️ Errore durante il salvataggio del file RAW, salto.")
                        continue
                    # Pulisce, divide, salva e restituisce i segmenti file univoci per ogni parte di contenuto
                    cleaned_paths = self.text_cleaner.process_file(raw_path)
                    #print(f"[DEBUG] cleaned_paths = {cleaned_paths} ({type(cleaned_paths)})")
                    if not cleaned_paths or not isinstance(cleaned_paths, list):
                        print(f"⚠️ Nessun file pulito trovato, salto.")
                        continue
                    # Crea metadata
                    self._append_metadata(cleaned_paths, title,item)


                    pages_downloaded += 1
                    time.sleep(random.uniform(1.5, 3.0))  # Anti ban
                except KeyboardInterrupt:
                    print("🛑 Interrotto manualmente.")
                    return
                except Exception as e:
                    print(f"❌ Errore durante download/parsing:\n  URL: {item}\n  {e}")
                    continue

        print(f"🏁 Fine. Totale file raccolti: {pages_downloaded}")

    def _validate_state(self):
        errors = []

        # Verifica che la tokenizer sia definita
        if not hasattr(self, 'tokenizer') or self.tokenizer is None:
            errors.append("❌ Tokenizer non inizializzata.")
        # Verifica che il file metadata esista (o crealo vuoto)
        if not self.METADATA_PATH.exists():
            try:
                self.METADATA_PATH.touch()
                print(f"📄 Creato file metadata vuoto: {self.METADATA_PATH}")
            except Exception as e:
                errors.append(f"❌ Impossibile creare il file metadata: {e}")

        if errors:
            for e in errors:
                print(e)
            raise RuntimeError("🛑 Stato interno non valido. Interrompo l'esecuzione.")
        
        self.duplicate_manager = DuplicateManager(self.RAW_DIR, size_hash=50,metadata_path=self.METADATA_PATH)

        print("✅ Stato iniziale del crawler valido.")

    def _download_page(self, url):

        try:

            crawler = StealthCrawler(mode="balanced")
            response = crawler.download_html(url)
            title = ""

            html = response
            domain = urlparse(url).netloc.replace("www.", "")
            soup = BeautifulSoup(html, "html.parser")

            if domain in SITE_PARSERS:
                print(f"🔍 Parsing personalizzato per {domain}")
                parsed = SITE_PARSERS[domain](soup)

                if not parsed:
                    print(f"⚠️ Il parser per {domain} ha restituito None")
                    return "", "", ""
                
                title = parsed["title"]

                content_div = parsed.get("text", [])

                if not content_div:
                    print(f"⚠️ Parser per {domain} ha restituito contenuto vuoto per {url}")
                    return "", title, ""
                
                print(f"✅ Parsed {domain} | Titolo: {title} | Tag estratti: {len(content_div)}")
                
                return self._markup_text(content_div,title, url)

            else:
                elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])

                return self._markup_text(elements)
            

        except Exception as e:
            print(f"⚠️ Errore download/parsing {url}: {e}")
            return "", "",""
        
    def _markup_text(self, elements: list, title: str = None, url:str = "") -> str:

        if not elements or not isinstance(elements, list):
            print(f"❌ markup_text ha ricevuto oggetto non iterabile o vuoto da URL: {url}")
            return "", title or "UNKNOWN", ""
        
        structured_lines = []
        
        elements = [el for el in elements if el and hasattr(el, "name")] # Filtra gli elementi non validi

        for el in elements:
           
            tag = el.name.lower()
            text = el.get_text(strip=True)

            if not text or len(text.split()) < 5: # Ignora testo corto o vuoto
                print(f"⚠️ Ignoro tag vuoto o corto: {tag} | Testo: {text}")
                continue


            classes = el.get("class", [])
            class_set = set(classes) if isinstance(classes, list) else {classes}

            # ⚠️ Mapping basato sulle classi HTML
            if class_set & {"post-single-summary", "news-subtitle", "post-subtitle"}:
                label = "SUBTITLE"
            elif class_set & {"post-single-text", "news-txt", "rich-text"}:
                label = "TEXT"
            elif class_set & {"section-header", "subsection"}:
                label = "SECTION"
            elif tag == "h1":
                label = "TITLE"
                if not title:
                    title = text
            elif tag in ["h2", "h3"]:
                label = "SUBTITLE"
            elif tag in ["h4", "h5", "h6"]:
                label = "SECTION"
            else:
                label = "TEXT"

            structured_lines.append(f"[{label}] {text}")

        # Titolo di fallback
        if not title:
            title = "UNKNOWN"
            print(f"⚠️ Nessun titolo trovato, uso 'UNKNOWN'")

        if len(structured_lines) < 2: # Se ci sono meno di 2 linee, ignora
            print(f"⚠️ Contenuto troppo scarno: {title}")
            return "", title, ""
        
        structured_text = "\n".join(structured_lines)

        if len(structured_text.split()) < 10: 
            print("⚠️ Contenuto ignorato: troppo breve dopo il markup.")
            return "", title, ""

        return structured_text, title, ""
    
    def _normalize_content(self,content):
        """
        Normalizza il contenuto:
        - converte in minuscolo
        - rimuove accenti (è → e)
        - rimuove punteggiatura e caratteri speciali
        - normalizza spazi multipli
        """
        # Minuscolo
        content = content.lower()

        # Rimuove accenti
        content = unicodedata.normalize('NFD', content)
        content = ''.join(c for c in content if unicodedata.category(c) != 'Mn')

        # Rimuove tutto ciò che non è alfanumerico o spazio
        content = re.sub(r'[^\w\s]', '', content)

        # Normalizza spazi multipli
        content = re.sub(r'\s+', ' ', content).strip()
    
        return content
    
    def _save_raw_text(self, name, text):

        filepath = self.RAW_DIR / f"{name}.txt"

        if self.duplicate_manager.is_duplicate_path(filepath):
            print(f"⚠️ File duplicato: {filepath}")
            return filepath
        
        self.duplicate_manager.register_path(filepath)
        self.duplicate_manager.register_content(self._normalize_content(text))

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text.strip())
        return filepath

    def _hash_string(self, s: str):
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    def _append_metadata(self, cleaned_paths: list[Path], title: str = "", url: str = ""):

        if not hasattr(self, 'tokenizer') or self.tokenizer is None:
            print("❌ Errore: tokenizer non definito!")
            return

        with open(self.METADATA_PATH, 'a', encoding='utf-8') as meta_file:
            

            for path in cleaned_paths:

                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                hash_value = self._hash_string(str(path))

                if self.duplicate_manager.is_duplicate_metadata(hash_value):
                    print(f"⚠️ Contenuto duplicato in {path}, salto.")
                    continue
                
                if not content or not isinstance(content, str):
                    print(f"⚠️ Contenuto vuoto o non valido nel file {path}")
                    continue
                    #print(f"[DEBUG] Contenuto in {path}:\n{content[:200]}")  # primi 200 caratteri
                
                self.duplicate_manager.register_metadata(hash_value)

                try:
                    tokens = self.tokenizer.tokenize(content)

                    if tokens is None:
                        print(f"❌ Tokenizer ha restituito None per {path}, per il contenuto: {content[:50]}")
                        continue

                    if not isinstance(tokens, list):
                        print(f"❌ Tokenizer ha restituito un tipo non valido: {type(tokens)} per {path}")
                        continue

                    if len(tokens) == 0:
                        print(f"⚠️ Nessun token trovato per {path}, contenuto ignorato.")
                        continue

                    metadata = {
                        "title": title or "UNKNOWN",
                        "path": str(path.resolve()),
                        "hash": hash_value,
                        "n_tokens": len(tokens),
                        "tokens": tokens,
                        "url": url or "UNKNOWN",
                    }

                    json.dump(metadata, meta_file, ensure_ascii=False)
                    meta_file.write('\n')

                except Exception as e:
                    print(f"❌ Errore durante _append_metadata per {path}: {e}")
    
    def _setup_folders(self):
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.CLEANED_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    

    