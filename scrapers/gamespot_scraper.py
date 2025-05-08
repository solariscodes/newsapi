import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class GameSpotScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.gamespot.com", "GameSpot")
    
    def get_article_urls(self, limit=10):
        soup = get_soup(f"{self.base_url}/news")
        if not soup:
            return []
        
        article_links = []
        # The structure has changed, now using different selectors
        articles = soup.select("a.card-item__link")
        
        if not articles:
            # Try alternative selectors
            articles = soup.select("a[data-event-tracking='Thumb Click']")
        
        if not articles:
            # Try another alternative
            articles = soup.select("a[href*='/articles/']")
        
        for article in articles:
            if len(article_links) >= limit:
                break
                
            url = article.get("href")
            if url:
                if not url.startswith("http"):
                    url = self.base_url + url
                if url not in article_links:  # Avoid duplicates
                    article_links.append(url)
        
        return article_links[:limit]
    
    def scrape_article(self, url):
        soup = get_soup(url)
        if not soup:
            return None
        
        # Extract title
        title_tag = soup.select_one("h1")
        title = title_tag.text.strip() if title_tag else ""
        
        # Extract image
        image_tag = soup.select_one("img.article-image")
        if not image_tag:
            image_tag = soup.select_one("picture img")
        if not image_tag:
            image_tag = soup.select_one("img[src*='gamespot']")
        
        image_url = ""
        if image_tag:
            image_url = image_tag.get("src", "")
            if not image_url and image_tag.get("data-src"):
                image_url = image_tag.get("data-src")
        
        # Extract content - focus on article text only
        # First, try to find the main article content container
        content_div = None
        
        # Try different selectors to find the article content
        for selector in ["div.article-body", "div.js-content-entity-body", "section.content-body", "div[data-id='article-body']"]:
            content_div = soup.select_one(selector)
            if content_div:
                break
                
        if not content_div:
            # If still not found, look for any div with 'body' in the class name
            for div in soup.select("div[class*='body']"):
                # Skip navigation or header elements
                if not any(cls in div.get('class', []) for cls in ['nav', 'header', 'footer', 'menu']):
                    content_div = div
                    break
        
        if content_div:
            # Remove unwanted elements
            for unwanted in content_div.select("div.ad-wrap, div.mapped-ad, div[class*='ad'], nav, header, footer, script, style"):
                if unwanted:
                    unwanted.decompose()
            
            # Try to get paragraphs first
            paragraphs = content_div.select("p")
            if paragraphs and len(paragraphs) > 1:  # Ensure we have meaningful content
                content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
            else:
                # If no paragraphs found or only one (might be a header), try getting text from other elements
                content = ""
                for elem in content_div.find_all(['p', 'h2', 'h3', 'li', 'span']):
                    if elem.text.strip() and len(elem.text.strip()) > 20:  # Only include substantial text
                        content += elem.text.strip() + " "
                content = content.strip()
        else:
            content = ""
        
        # Validate title and image_url before returning
        if not is_valid_title(title) or not is_valid_image_url(image_url):
            print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
            return None
            
        return create_article_object(title, image_url, content, url, self.name)
