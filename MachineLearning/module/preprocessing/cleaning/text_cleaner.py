# 📂 module/preprocessing/cleaning/text_cleaner.py
import os
import re
from pathlib import Path

class TextCleaner:
    def __init__(self, min_sentence_length=30, min_block_length=200, clean_wiki_markup=False):
        self.min_sentence_length = min_sentence_length
        self.min_block_length = min_block_length
        self.clean_wiki_markup = clean_wiki_markup

    def clean_text(self, text):
        if self.clean_wiki_markup:
            text = self._clean_wikipedia_markup(text)
        text = re.sub(r'[\r\n]+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    #def split_sentences(self, text):
       #sentences = re.split(r'(?<=[.!?])\s+', text)
        #return [s.strip() for s in sentences if s.strip()]
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
    
    def process_file(self, filepath: Path, domain: str = None):
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        buffer = ""
        segments = []
        count = 0
        cleaned_dir = Path("data/dataset_italiano/cleaned")
        os.makedirs(cleaned_dir, exist_ok=True)

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
                clean_file = cleaned_dir / (filepath.stem + f"_part_{count}.txt")
                with open(clean_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(buffer.strip())
                segments.append(clean_file)
                buffer = ""
                count += 1

        if buffer.strip():
            clean_file = cleaned_dir / (filepath.stem + f"_part_{count}.txt")
            with open(clean_file, 'w', encoding='utf-8') as f_out:
                f_out.write(buffer.strip())
            segments.append(clean_file)

        return segments

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
