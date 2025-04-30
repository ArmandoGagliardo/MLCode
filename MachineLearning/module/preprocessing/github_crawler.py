import os
import json
import requests
from pathlib import Path
from module.preprocessing.parser_manager import get_parser
from tqdm import tqdm
import hashlib
# ======== CONFIG ========
OUTPUT_DIR = Path("dataset")
OUTPUT_DIR.mkdir(exist_ok=True)
RAW_DIR = OUTPUT_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "dataset_github.json"
MAX_FILES_PER_REPO = 20
BRANCH = "main"

# Supportati
EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".java": "java",
    ".sh": "shell",
    ".cpp": "cpp",
    ".php": "php",
    ".rb": "ruby",
    ".go": "go",
}

REPOS = [
     # JavaScript
    "facebook/react",
    "vercel/next.js",
    # Java
    "spring-projects/spring-framework",
    "elastic/elasticsearch",
    # Shell
    "ohmyzsh/ohmyzsh",
    #python 
    "psf/requests",
    "pallets/flask",
    "tiangolo/fastapi",
    "numpy/numpy",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "encode/httpx",
    "matplotlib/matplotlib",
    "Textualize/rich",
    "sympy/sympy",
    "openai/openai-python",
    "pyca/cryptography",
    "sqlalchemy/sqlalchemy",
    "python/cpython",
    "huggingface/transformers",
    # c++
    "electron/electron",               # C++ + JS (molto vasto)
    "opencv/opencv",                   # Libreria di visione artificiale
    "TheCherno/Hazel",                 # Motore grafico
    "fmtlib/fmt",                      # Libreria per formattazione
    "google/googletest",               # Libreria testing
    "swoole/swoole-src",                # Estensione PHP in C++
    # php
    "laravel/framework",               # Il framework PHP più famoso
    "symfony/symfony",                 # Alternativa enterprise
    "fzaninotto/Faker",                # Generatore di dati fake
    "guzzle/guzzle",                   # Client HTTP
    "php/php-src",                     # Sorgente del linguaggio
    "barryvdh/laravel-debugbar",       # Debug per Laravel
    # ruby
    "rails/rails",                     # Web framework
    "jekyll/jekyll",                   # Generatore di siti statici
    "rubocop/rubocop",                 # Linter/formatter
    "Homebrew/brew",                   # Gestore pacchetti
    "discourse/discourse",            # Forum software
    "fastlane/fastlane",               # DevOps per mobile
    # go
    "golang/go",                       # Il linguaggio stesso
    "gin-gonic/gin",                   # Web framework
    "spf13/cobra",                     # CLI framework
    "harness/drone",                   # CI/CD in Go
    "goharbor/harbor",                # Registry container
    "go-kit/kit"                       # Toolkit microservizi

]

GITHUB_API = "https://api.github.com/repos"
HEADERS = {
    "Accept": "application/vnd.github.v3.raw",
    "Authorization": "token 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",
    "User-Agent": "github-crawler"
}

def save_raw_file(repo, path, content):
    """Salva il file sorgente grezzo localmente."""
    safe_repo = repo.replace("/", "_")
    repo_dir = RAW_DIR / safe_repo
    repo_dir.mkdir(parents=True, exist_ok=True)
    file_name = path.replace("/", "_")
    with open(repo_dir / file_name, "w", encoding="utf-8") as f:
        f.write(content)

def get_files(repo):
    """Recupera la lista dei file sorgente compatibili da un repo."""
    files = []
    url = f"{GITHUB_API}/{repo}/git/trees/{BRANCH}?recursive=1"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"⚠️ Impossibile accedere a {repo}")
        return []
    data = res.json()
    for item in data.get("tree", []):
        path = item["path"].lower()
        ext = Path(path).suffix
        if ext in EXTENSIONS and all(x not in path for x in ["test", "__init__", "setup"]):
            files.append(item["path"])
    return files[:MAX_FILES_PER_REPO]

def download_file(repo, path):
    """Scarica il contenuto grezzo di un file."""
    url = f"https://raw.githubusercontent.com/{repo}/{BRANCH}/{path}"
    res = requests.get(url)
    return res.text if res.status_code == 200 else None

def extract_functions(source_code, extension):
    """Esegue il parsing del codice usando il parser specifico per estensione."""
    parser = get_parser(extension)
    if not parser:
        print(f"⚠️ Parser non trovato per {extension}")
        return []
    try:
        return parser.parse(source_code)
    except Exception as e:
        print(f"⚠️ Errore nel parsing: {e}")
        return []

def crawl():
    """Esegue la scansione di tutti i repository definiti in REPOS."""
    # All'inizio del crawl()
    existing_hashes = set()
    dataset = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            dataset = json.load(f)
            for item in dataset:
                h = hashlib.sha256((item["input"] + item["output"]).encode("utf-8")).hexdigest()
                existing_hashes.add(h)
    for repo in tqdm(REPOS, desc="🔍 Scansione repository"):
        print(f"\n📁 {repo}")
        files = get_files(repo)
        for path in files:
            extension = Path(path).suffix
            code = download_file(repo, path)
            if not code:
                continue
            save_raw_file(repo, path, code)
            for func in extract_functions(code, extension):
                if len(func.get("input", "")) > 10 and len(func.get("output", "")) > 10:
                    h = hashlib.sha256((func["input"] + func["output"]).encode("utf-8")).hexdigest()
                    if h not in existing_hashes:
                        dataset.append(func)
                        existing_hashes.add(h)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Salvato: {len(dataset)} funzioni in {OUTPUT_FILE}")

if __name__ == "__main__":
    crawl()
