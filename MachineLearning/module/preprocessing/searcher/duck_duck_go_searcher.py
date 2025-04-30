# 📂 module/preprocessing/searcher.py
import requests
from bs4 import BeautifulSoup
import random
import time
import urllib.parse

class DuckDuckGoSearcher:
    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"

    def search(self, keywords: str, max_results: int = 5):
        time.sleep(random.uniform(1, 2))
        params = {
    "q": keywords,
    "kl": "it-it",  # Forza contenuti italiani
    "hl": "it"      # Forza interfaccia italiana
}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            print(f"🔍 Ricerca per: {keywords}")
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Errore durante la ricerca DuckDuckGo: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/l/?" in href:
                parsed = urllib.parse.urlparse(href)
                query = urllib.parse.parse_qs(parsed.query)
                real_url = query.get("uddg", [""])[0]
                real_url = urllib.parse.unquote(real_url)
                if real_url.startswith("http"):
                    links.append(real_url)
            elif href.startswith("http"):
                links.append(href)

            if len(links) >= max_results:
                break

        return links
