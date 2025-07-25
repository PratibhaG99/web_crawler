import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import queue

class WebCrawler:
    def __init__(self, base_url, max_threads=5, max_pages=20):
        self.base_url = base_url
        self.visited = set()
        self.lock = threading.Lock()
        self.q = queue.Queue()
        self.max_threads = max_threads
        self.max_pages = max_pages
        self.page_count = 0

        if not os.path.exists('pages'):
            os.makedirs('pages')

    def fetch_page(self, url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text
            else:
                return response.content 
        except requests.RequestException:
            return None

    def save_page(self, url, content):
        parsed = urlparse(url)
        filename = parsed.netloc.replace('.', '_') + parsed.path.replace('/', '_')
        if not filename:
            filename = 'index'
        filename = filename[:100]  # limit filename length
        with open(f'pages/{filename}.html', 'w', encoding='ascii') as f:  
            f.write(content)

    def crawl_page(self):
        while True:
            try:
                url = self.q.get(timeout=10)
            except queue.Empty:
                return

            if url in self.visited or self.page_count >= self.max_pages:
                self.q.task_done()
                continue
            self.visited.add(url)
            self.page_count += 1

            print(f"Crawling: {url}")
            content = self.fetch_page(url)
            if content:
                self.save_page(url, content)
                soup = BeautifulSoup(content, 'html.parser')
                for link_tag in soup.find_all('a', href=True):
                    link = urljoin(url, link_tag['href'])
                    if urlparse(link).netloc == urlparse(self.base_url).netloc:
                        self.q.put(link)  
            self.q.task_done()

    def start(self):
        self.q.put(self.base_url)
        threads = []

        for _ in range(self.max_threads):
            t = threading.Thread(target=self.crawl_page)
            t.start()
            threads.append(t)

        self.q.join()

        for t in threads:
            t.join()

if __name__ == "__main__":
    start_url = " https://en.wikipedia.org/wiki/Artificial_intelligence#Deep_learning"
    crawler = WebCrawler(start_url, max_threads=5, max_pages=20)
    crawler.start()