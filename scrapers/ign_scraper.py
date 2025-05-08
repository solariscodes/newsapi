import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text
from scrapers.base_scraper import BaseScraper

class IGNScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.ign.com", "IGN")
    
    def get_article_urls(self, limit=10):
        soup = get_soup(f"{self.base_url}/news")
        if not soup:
            return []
        
        article_links = []
        articles = soup.select("div.content-item")
        
        for article in articles:
            # If limit is None, get all articles, otherwise respect the limit
            if limit is not None and len(article_links) >= limit:
                break
                
            link_tag = article.select_one("a")
            if link_tag and link_tag.get("href"):
                url = link_tag["href"]
                if not url.startswith("http"):
                    url = self.base_url + url
                article_links.append(url)
        
        # If limit is None, return all articles, otherwise respect the limit
        return article_links if limit is None else article_links[:limit]
    
    def scrape_article(self, url):
        soup = get_soup(url)
        if not soup:
            return None
        
        # Extract title
        title_tag = soup.select_one("h1.article-title")
        if not title_tag:
            title_tag = soup.select_one("h1.display-title")
        title = title_tag.text if title_tag else ""
        
        # Extract image - try multiple selectors
        image_url = ""
        for img_selector in ["div.article-header img", "div.article-lead-image-wrap img", "figure.article-image img", 
                            "meta[property='og:image']", "meta[name='twitter:image']", "div.jsx-3553238252 img", 
                            "div.article-page img", "picture img", "div.jsx-3553238252 picture source"]:
            image_tag = soup.select_one(img_selector)
            if image_tag:
                if img_selector in ["meta[property='og:image']", "meta[name='twitter:image']"]:
                    image_url = image_tag.get("content", "")
                elif img_selector == "div.jsx-3553238252 picture source":
                    image_url = image_tag.get("srcset", "").split(" ")[0] if image_tag.get("srcset") else ""
                else:
                    image_url = image_tag.get("data-src") or image_tag.get("srcset", "").split(" ")[0] or image_tag.get("src", "")
                if image_url:
                    break
        
        # If still no image, try to find any image in the article
        if not image_url:
            for img in soup.select("img"):
                potential_url = img.get("data-src") or img.get("srcset", "").split(" ")[0] or img.get("src", "")
                if potential_url and (".jpg" in potential_url or ".png" in potential_url or ".webp" in potential_url):
                    image_url = potential_url
                    break
        
        # If still no image, use a default image
        if not image_url:
            image_url = "https://assets-prd.ignimgs.com/2023/09/20/ign-default-1695238495427.jpg"  # Default IGN image
        
        # Extract content
        content_div = soup.select_one("div.article-content")
        if not content_div:
            content_div = soup.select_one("div.article-page")
        
        if content_div:
            # Remove unwanted elements
            for unwanted in content_div.select("div.ad-wrap, div.widget, div.sidebar, script, style"):
                unwanted.decompose()
            
            paragraphs = content_div.select("p")
            content = " ".join([p.text for p in paragraphs])
        else:
            content = ""
        
        return create_article_object(title, image_url, content, url, self.name)
