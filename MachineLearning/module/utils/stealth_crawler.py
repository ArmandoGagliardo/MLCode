# 📂 module/utils/stealth_crawler.py

import random
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class StealthCrawler:
    def __init__(self, mode="balanced"):
        self.user_agents = self._load_user_agents()
        self.session = self._init_session()
        self.mode = mode  # "aggressive", "balanced", "slow"
        self._setup_logger()

    def _load_user_agents(self):
        return [
            # Desktop
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36",
            # Mobile
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.136 Mobile Safari/537.36"
        ]

    def _init_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 403, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1.5
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _setup_logger(self):
        self.logger = logging.getLogger("StealthCrawler")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def get(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["User-Agent"] = random.choice(self.user_agents)

        self._sleep_before_request()
        self.logger.info(f"Requesting: {url}")

        try:
            response = self.session.get(url, headers=headers, timeout=15, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request failed: {e}")
            return None

    def _sleep_before_request(self):
        if self.mode == "aggressive":
            time.sleep(random.uniform(0.5, 1.2))
        elif self.mode == "balanced":
            time.sleep(random.uniform(1.5, 3.0))
        elif self.mode == "slow":
            time.sleep(random.uniform(3.0, 6.0))

    def download_html(self, url):
        response = self.get(url)
        return response.text if response else None
