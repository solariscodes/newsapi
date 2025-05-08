from abc import ABC, abstractmethod
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object

class BaseScraper(ABC):
    """
    Base class for all website scrapers
    """
    def __init__(self, base_url, name=None):
        self.base_url = base_url
        self.name = name or self._extract_name_from_url(base_url)
    
    def _extract_name_from_url(self, url):
        """Extract a name from the URL"""
        import re
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Extract the main domain name without TLD
        match = re.search(r'([^.]+)', domain)
        if match:
            return match.group(1).capitalize()
        return domain
    
    @abstractmethod
    def get_article_urls(self, limit=10):
        """
        Get a list of article URLs from the website
        
        Args:
            limit (int): Maximum number of articles to scrape
            
        Returns:
            list: List of article URLs
        """
        pass
    
    @abstractmethod
    def scrape_article(self, url):
        """
        Scrape a single article
        
        Args:
            url (str): URL of the article to scrape
            
        Returns:
            dict: Article data with title, image_url, content, source_url, source_name
        """
        pass
    
    def scrape(self, limit=10):
        """
        Scrape articles from the website
        
        Args:
            limit (int or None): Maximum number of articles to scrape, None for unlimited
            
        Returns:
            list: List of article data
        """
        print(f"Scraping {self.name}...")
        
        # Get article URLs - handle None limit case
        article_urls = self.get_article_urls(limit)
        
        if not article_urls:
            print(f"No articles found on {self.name}")
            return []
        
        print(f"Found {len(article_urls)} articles on {self.name}")
        
        # Scrape each article
        articles = []
        for i, url in enumerate(article_urls):
            print(f"  Scraping article {i+1}/{len(article_urls)}: {url}")
            try:
                article = self.scrape_article(url)
                if article:
                    articles.append(article)
            except Exception as e:
                print(f"  Error scraping article {url}: {e}")
        
        print(f"Successfully scraped {len(articles)} articles from {self.name}")
        return articles
