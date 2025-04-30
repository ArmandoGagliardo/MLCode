# 📂 module/preprocessing/searcher/website_searcher.py

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from urllib.parse import unquote
import re
from module.utils.stealth_crawler import StealthCrawler

class WebsiteSearcher:
    def __init__(self, base_url: str, domain_filter: str = None, max_links: int = 30, deep: bool = True):
        self.base_url = base_url
        self.domain_filter = domain_filter or urlparse(base_url).netloc
        self.max_links = max_links
        self.deep = deep
        self.visited = set()

    def search(self, keyword: str = None):

        self.keyword = keyword.lower().strip()

        print(f"🌐 Inizio ricerca su {self.base_url} per Keyword: {keyword}")
        initial_links = self._extract_links(self.base_url)

        if not self.deep:
            return list(initial_links)[:self.max_links]

        all_links = set(initial_links)
        
        for link in list(initial_links):
            if len(all_links) >= self.max_links:
                break
            child_links = self._extract_links(link)
            all_links.update(child_links)
            time.sleep(random.uniform(0.8, 1.5))  # evita ban

        print(f"🔗 Totale link raccolti: {len(all_links)}")
        return list(all_links)[:self.max_links]


    def _normalize_url_text(self,text: str) -> str:
        text = text.lower()
        text = re.sub(r'[-_/%20]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_links(self, page_url: str):

        keyword = self.keyword
        links = set()
        blacklist_substrings = [
            "#", "javascript:",
            "/video/", "/videogallery/", "/foto/", "/gallery/", 
            "/immagini/", "/immagine/", "/speciali/", "/archivio/"
        ]
        if page_url in self.visited:
            return links
        
        self.visited.add(page_url)

        try:
            crawler = StealthCrawler(mode="balanced")
            response = crawler.download_html(page_url)
            soup = BeautifulSoup(response, "html.parser")
        except Exception as e:
            print(f"⚠️ Errore su {page_url}: {e}")
            return links

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(page_url, href)
            parsed = urlparse(full_url)

            if self.domain_filter not in parsed.netloc:
                continue
            if any(sub in full_url for sub in blacklist_substrings):
                continue

            # Normalizza contenuti per matching

            slug = self._normalize_url_text(unquote(full_url))
            #print(f"[DEBUG] Keyword: {self.keyword} | Slug: {slug} | Match: {self.keyword in slug}")
            link_text = self._normalize_url_text(a.get_text(strip=True))

            #words = keyword.lower().split()

            #if not any(word in slug for word in words) and not any(word in link_text for word in words):
                #continue
            if not any(kw in slug or kw in link_text for kw in keyword.split()):
                continue

            links.add(full_url)

            if len(links) >= self.max_links:
                break

        print(f"🔎 {len(links)} link trovati {links}")
        return links
