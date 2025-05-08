import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class PCGamerScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.pcgamer.com", "PC Gamer")
    
    def get_article_urls(self, limit=10):
        soup = get_soup(f"{self.base_url}/news")
        if not soup:
            return []
        
        article_links = []
        articles = soup.select("div.listingResult")
        
        for article in articles:
            # If limit is None, get all articles, otherwise respect the limit
            if limit is not None and len(article_links) >= limit:
                break
                
            link_tag = article.select_one("a.article-link")
            if link_tag and link_tag.get("href"):
                url = link_tag["href"]
                if not url.startswith("http"):
                    url = self.base_url + url
                article_links.append(url)
        
        return article_links[:limit]# If limit is None, return all articles, otherwise respect the limit
        return article_links if limit is None else article_links[:limit]
    
    def scrape_article(self, url):
        soup = get_soup(url)
        if not soup:
            return None
        
        # Extract title
        title_tag = soup.select_one("h1.article-name")
        if not title_tag:
            title_tag = soup.select_one("h1.article-title")
        if not title_tag:
            title_tag = soup.select_one("h1")
        title = title_tag.text.strip() if title_tag else ""
        
        # Extract image - try multiple selectors
        image_url = ""
        for img_selector in ["figure.lead-image img", "div.image-wrap img", "picture img", 
                            "meta[property='og:image']", "div.article-hero img", "div.featured-image img"]:
            image_tag = soup.select_one(img_selector)
            if image_tag:
                if img_selector == "meta[property='og:image']":
                    image_url = image_tag.get("content", "")
                else:
                    image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                if image_url:
                    break
        
        # If still no image, try to find any image in the article
        if not image_url:
            for img in soup.select("img"):
                potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                if potential_url and (".jpg" in potential_url or ".png" in potential_url or ".webp" in potential_url):
                    if potential_url.startswith("//"):
                        potential_url = "https:" + potential_url
                    image_url = potential_url
                    break
        
        # If still no image, use a default image
        if not image_url:
            image_url = "https://cdn.mos.cms.futurecdn.net/6bxva8DmZvNj8kaVrQZZMP-970-80.jpg"  # PC Gamer logo/default image
        
        # Extract content
        content_div = soup.select_one("div#article-body")
        
        if content_div:
            # Remove unwanted elements
            for unwanted in content_div.select("div.ad-container, div.related-articles, div.buying-guide, script, style"):
                if unwanted:
                    unwanted.decompose()
            
            paragraphs = content_div.select("p")
            content = " ".join([p.text for p in paragraphs])
        else:
            content = ""
        
        # Validate title and image_url before returning
        if not is_valid_title(title) or not is_valid_image_url(image_url):
            print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
            return None
            
        return create_article_object(title, image_url, content, url, self.name)
