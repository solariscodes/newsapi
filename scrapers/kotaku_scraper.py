import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class KotakuScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://kotaku.com", "Kotaku")
    
    def get_article_urls(self, limit=10):
        soup = get_soup(self.base_url)
        if not soup:
            return []
        
        article_links = []
        articles = soup.select("article.js_post_item")
        
        for article in articles:
            if len(article_links) >= limit:
                break
                
            link_tag = article.select_one("a.js_link")
            if link_tag and link_tag.get("href"):
                url = link_tag["href"]
                if not url.startswith("http"):
                    url = self.base_url + url
                article_links.append(url)
        
        return article_links[:limit]
    
    def scrape_article(self, url):
        soup = get_soup(url)
        if not soup:
            return None
        
        # Extract title
        title_tag = soup.select_one("h1.sc-1efpnfq-0")
        title = title_tag.text if title_tag else ""
        
        # Extract image
        image_tag = soup.select_one("div.sc-1i9kpqh-0 img")
        if not image_tag:
            image_tag = soup.select_one("picture img")
        
        image_url = ""
        if image_tag:
            image_url = image_tag.get("src", "")
        
        # Extract content
        content_div = soup.select_one("div.sc-r43lxo-1")
        
        if content_div:
            # Remove unwanted elements
            for unwanted in content_div.select("aside, div.ad-container, script, style"):
                if unwanted:
                    unwanted.decompose()
            
            paragraphs = content_div.select("p")
            content = " ".join([p.text for p in paragraphs])
        else:
            content = ""
        
        # Validate title and image_url
        if not is_valid_title(title) or not is_valid_image_url(image_url):
            return None
        return create_article_object(title, image_url, content, url, self.name)
