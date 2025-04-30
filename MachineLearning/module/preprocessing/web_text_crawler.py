import time
import random
import hashlib
import json
from bs4 import BeautifulSoup
from pathlib import Path
from module.preprocessing.cleaning.text_cleaner import TextCleaner
from transformers import AutoTokenizer
from urllib.parse import urlparse
from module.utils.stealth_crawler import StealthCrawler

def _parse_ansa(soup: BeautifulSoup) -> dict:
    title_tag = soup.find("h1", class_=["news-title", "post-single-title"])
    title = title_tag.get_text(strip=True) if title_tag else "UNKNOWN"

    # Cerca tutti i div possibili
    content_blocks = soup.find_all("div", class_=[
        "post-single-text", "news-txt", "post-single-summary", "rich-text news-txt"
    ])

    # Se trova almeno uno, restituisci la lista
    if content_blocks:
        return {"title": title, "text": content_blocks}

    # Fallback: trova tutti i tag testuali
    fallback = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])
    return {"title": title, "text": fallback}
# Mappa dominio → funzione parser
SITE_PARSERS = {
    "ansa.it": _parse_ansa,
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
        self.text_cleaner = TextCleaner()
        self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-italian-cased")
        self.seen_hashes = self._load_seen_hashes()
        self._setup_folders()
        self._validate_state()

    def crawl(self, keywords: list[str]):

        self.seen_hashes = self._load_seen_hashes()
        
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
                    try:
                        self._append_metadata(cleaned_paths, title)
                    except Exception as e:
                        print(f"❌ Errore durante _append_metadata per {cleaned_paths}:\n  {e}")
                        continue

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

        # Verifica che seen_hashes sia un set
        if not isinstance(self.seen_hashes, set):
            errors.append(f"❌ seen_hashes non è un set ma {type(self.seen_hashes)}")

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
        
    def _markup_text(self, elements: list, title: str = "", url:str = "") -> str:
        if not elements or not isinstance(elements, list):
            print(f"❌ markup_text ha ricevuto oggetto non iterabile o vuoto da URL: {url}")
            return "", title or "UNKNOW", ""
        structured_lines = []
        title = title.strip()
        elements = [el for el in elements if el and hasattr(el, "name")]
        for el in elements:
           
            tag = el.name.lower()
            text = el.get_text(strip=True)

            if not text or len(text.split()) < 5:
                print(f"⚠️ Ignoro tag vuoto o corto: {tag} | Testo: {text}")
                continue

            # Assegna il label
            if title:
                label = "SUBTITLE" if tag in ["h2", "h3"] else "SECTION" if tag in ["h4", "h5", "h6"] else "TEXT"
            else:
                if tag == "h1":
                    label = "TITLE"
                    title = text  # salva il titolo la prima volta che lo trovi
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

        if len(structured_lines) < 2:
            print(f"⚠️ Contenuto troppo scarno: {title}")
            return "", title, ""
        
        structured_text = "\n".join(structured_lines)

        if len(structured_text.split()) < 10:
            print("⚠️ Contenuto ignorato: troppo breve dopo il markup.")
            return "", title, ""

        return structured_text, title, ""
    
    def _save_raw_text(self, name, text):
        filepath = self.RAW_DIR / f"{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text.strip())
        return filepath

    def _hash_string(self, s: str):
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    def _append_metadata(self, cleaned_paths: list[Path], title: str = ""):

        if not hasattr(self, 'tokenizer') or self.tokenizer is None:
            print("❌ Errore: tokenizer non definito!")
            return

        with open(self.METADATA_PATH, 'a', encoding='utf-8') as meta_file:
            for path in cleaned_paths:

                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content or not isinstance(content, str):
                        print(f"⚠️ Contenuto vuoto o non valido nel file {path}")
                        continue
                    #print(f"[DEBUG] Contenuto in {path}:\n{content[:200]}")  # primi 200 caratteri

                if not content:
                    print(f"⚠️ File vuoto: {path}")
                    continue
                hash_value = self._hash_string(content)

                if self._is_duplicate(hash_value):
                    print(f"⚠️ File duplicato: {path}")
                    continue
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
                        "tokens": tokens
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

    def _is_duplicate(self, text: str) -> bool:
        if text in self.seen_hashes: ## Se il testo è già stato visto, è un duplicato, ITERAZIONE 
            return True
        self.seen_hashes.add(text)
        return False
    
    def _load_seen_hashes(self):
        self.seen_hashes = set()

        if not self.METADATA_PATH.exists():
            return self.seen_hashes  # 🔁 Ritorna set vuoto

        with open(self.METADATA_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if "hash" in entry:
                        self.seen_hashes.add(entry["hash"])
                except json.JSONDecodeError:
                    continue
        return self.seen_hashes

    