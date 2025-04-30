# module/preprocessing/crawlers/base_crawler.py

from abc import ABC, abstractmethod
from pathlib import Path



class BaseCrawler(ABC):

    OUTPUT_DIR = Path("dataset")
    OUTPUT_DIR.mkdir(exist_ok=True)
    RAW_DIR = OUTPUT_DIR / "raw"
    RAW_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE = OUTPUT_DIR / "dataset_github.json"
    MAX_FILES_PER_REPO = 20
    BRANCH = "main"

    @abstractmethod
    def crawl(self) -> list:
        """
        Ritorna una lista di dizionari in formato standardizzato:
        {
            "task_type": "code_generation",
            "language": "python",
            "func_name": "nome",
            "input": "docstring",
            "output": "codice"
        }
        """
        pass
