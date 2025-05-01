# 📂 module/preprocessing/cleaning/text_cleaner.py
import os
import re
from pathlib import Path
import unicodedata
from module.scripts.duplicate_manager import DuplicateManager

class TextCleaner:
    def __init__(self, min_sentence_length=30, min_block_length=200, clean_wiki_markup=False,cleaned_dir:Path = Path("data/dataset_italiano/cleaned")):
        self.min_sentence_length = min_sentence_length
        self.min_block_length = min_block_length
        self.clean_wiki_markup = clean_wiki_markup
        self.cleaned_dir = cleaned_dir
        self.duplicate_manager = DuplicateManager(cleaned_dir)

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

    def clean_text(self, text):
        if self.clean_wiki_markup:
            text = self._clean_wikipedia_markup(text)
        text = re.sub(r'[\r\n]+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_sentences(self, text):
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = []
        buffer = ""

        for s in raw_sentences:
            s = s.strip()
            if not s:
                continue

            # Se buffer è vuoto, inizia
            if not buffer:
                buffer = s
                continue

            # Se frase inizia minuscola → probabile continuazione
            if s and s[0].islower():
                buffer += " " + s
            else:
                sentences.append(buffer)
                buffer = s

        if buffer:
            sentences.append(buffer)

        return [s.strip() for s in sentences if len(s.strip()) >= self.min_sentence_length]
    
    def _save_segment(self,buffer,segment_index,raw_path_file:Path = None):

        if not buffer.strip():
            return 
        
        clean_file = self.cleaned_dir / (raw_path_file.stem + f"_part_{segment_index}.txt")

        normalized_buffer = self._normalize_content(buffer.strip())

        if self.duplicate_manager.is_duplicate_path(clean_file) or self.duplicate_manager.is_duplicate_content(normalized_buffer):
            print(f"[SKIP] Il file {clean_file} o il contenuto {normalized_buffer[:50]} è duplicato e non verrà scritto.")
            return clean_file


        with open(clean_file, 'w', encoding='utf-8') as f_out:
            f_out.write(normalized_buffer)
            
        self.duplicate_manager.register_content(normalized_buffer)
        self.duplicate_manager.register_path(clean_file)
        self.segments.append(clean_file)
        
    def process_file(self, raw_path_file: Path, domain: str = None):


        with open(raw_path_file, 'r', encoding='utf-8') as f: # Legge il file raw 
            raw_lines = f.readlines()

        buffer = ""
        self.segments = []
        count = 0
        
        os.makedirs(self.cleaned_dir, exist_ok=True)

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("[TITLE]"):
                content = self.clean_text(line[len("[TITLE]"):].strip())
                buffer += f"\n# {content}\n"

            elif line.startswith("[SUBTITLE]"):
                content = self.clean_text(line[len("[SUBTITLE]"):].strip())
                buffer += f"\n## {content}\n"

            elif line.startswith("[SECTION]"):
                content = self.clean_text(line[len("[SECTION]"):].strip())
                buffer += f"\n### {content}\n"

            elif line.startswith("[TEXT]"):
                content = self.clean_text(line[len("[TEXT]"):].strip())
                for sentence in self.split_sentences(content):
                    buffer += sentence + " "

            if len(buffer) >= self.min_block_length:

                self._save_segment(buffer, count,raw_path_file)
                buffer = ""
                count += 1

        self._save_segment(buffer, count,raw_path_file) # Salva l'ultimo buffer se non vuoto

        return self.segments

    def _clean_wikipedia_markup(self, text: str) -> str:
        print("🧹 Pulizia del testo Wikipedia...")
        # Rimuove file/media tipo [File:...]
        text = re.sub(r'\[\[File:[^\[\]]*\]\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[\[Image:[^\[\]]*\]\]', '', text, flags=re.IGNORECASE)

        # Rimuove template tipo {{...}}
        text = re.sub(r'\{\{[^{}]*\}\}', '', text)

        # Rimuove tag HTML tipo <ref>...</ref> o <...>
        text = re.sub(r'<[^>]+>', '', text)

        # Rimuove link interni [[...]]
        text = re.sub(r'\[\[[^\[\]]+\]\]', '', text)

        # Rimuove categorie
        text = re.sub(r'\[\[Categoria:[^\]]+\]\]', '', text, flags=re.IGNORECASE)

        # Rimuove entità HTML tipo &nbsp;
        text = re.sub(r'&[a-z]+;', ' ', text)

        # Rimuove parentesi "orfane" o senza contenuto
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)

        # Normalizza spazi multipli
        text = re.sub(r'\s+', ' ', text)

        # Ripulisce doppie punteggiature
        text = re.sub(r'\. \.', '.', text)
        text = re.sub(r', ,', ',', text)
        return text
