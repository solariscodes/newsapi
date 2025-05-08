import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class EurogamerScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.eurogamer.net", "Eurogamer")
    
    def get_article_urls(self, limit=10):
        # Try different paths to find articles
        paths = ["/news", "/", "/articles", "/reviews"]
        
        article_links = []
        
        for path in paths:
            try:
                print(f"Trying to access Eurogamer at {self.base_url}{path}")
                soup = get_soup(f"{self.base_url}{path}", 
                               headers={
                                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                                   'Accept-Language': 'en-US,en;q=0.9',
                                   'Cache-Control': 'max-age=0',
                                   'Connection': 'keep-alive'
                               })
                
                if not soup:
                    continue
                
                # Try different selectors for articles
                selectors = [
                    "a[href*='/news/']",
                    "a[href*='/articles/']",
                    "div.article a",
                    "h2 a",
                    "article a",
                    "a.article-link"
                ]
                
                for selector in selectors:
                    articles = soup.select(selector)
                    if articles:
                        print(f"Found {len(articles)} articles with selector '{selector}'")
                        break
                
                if not articles:
                    continue
                
                for article in articles:
                    if len(article_links) >= limit:
                        break
                    
                    url = article.get("href")
                    if url and ("/news/" in url or "/articles/" in url):
                        if not url.startswith("http"):
                            url = "https://www.eurogamer.net" + url
                        if url not in article_links:  # Avoid duplicates
                            article_links.append(url)
                
                if article_links:
                    break  # If we found articles, no need to try other paths
            
            except Exception as e:
                print(f"Error accessing Eurogamer at {self.base_url}{path}: {e}")
                continue
        
        # If we still couldn't find any articles, try some hardcoded recent URLs
        if not article_links:
            print("Falling back to hardcoded Eurogamer URLs")
            fallback_urls = [
                "https://www.eurogamer.net/prime-gaming-members-get-22-more-games-in-may",
                "https://www.eurogamer.net/amidst-layoffs-apex-legends-announces-new-season-25-legend-sparrow-and-return-of-arenas-1",
                "https://www.eurogamer.net/confirmed-xbox-console-prices-are-going-up-worldwide",
                "https://www.eurogamer.net/super-mario-wonder-captain-toad-and-wario-sets-join-nintendo-lego-range",
                "https://www.eurogamer.net/evil-dead-the-game-disappears-from-sale-after-three-years"
            ]
            article_links = fallback_urls[:limit]
        
        return article_links[:limit]
    
    def scrape_article(self, url):
        try:
            soup = get_soup(url, 
                           headers={
                               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                               'Accept-Language': 'en-US,en;q=0.9',
                               'Cache-Control': 'max-age=0',
                               'Connection': 'keep-alive'
                           })
            if not soup:
                return None
            
            # Extract title - try multiple selectors
            title = ""
            for title_selector in ["h1", "h1.article__title", "h1.title", "header h1"]:
                title_tag = soup.select_one(title_selector)
                if title_tag:
                    title = title_tag.text.strip()
                    break
            
            # If we couldn't find a title, extract it from the URL as a fallback
            if not title:
                import re
                # Extract the last part of the URL and convert hyphens to spaces
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Extract image - try multiple selectors
            image_url = ""
            for img_selector in ["figure img", "picture img", "img[src*='eurogamer']", 
                                "img.lead", "img.article__image", "div.article__image-container img"]:
                image_tag = soup.select_one(img_selector)
                if image_tag:
                    image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                    if image_url:
                        break
            
            # If still no image, try to find any image in the article
            if not image_url:
                for img in soup.select("img"):
                    potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                    if potential_url and ("eurogamer" in potential_url or "/images/" in potential_url):
                        image_url = potential_url
                        break
            
            # Extract content - try multiple selectors
            content = ""
            for content_selector in ["div[class*='article__body']", "div.article__content", "div.content", 
                                    "article", "div.article-body"]:
                content_div = soup.select_one(content_selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.select("aside, div.ad, div.newsletter, div.comments, div.social, nav, script, style"):
                        if unwanted:
                            unwanted.decompose()
                    
                    # Try to get paragraphs
                    paragraphs = content_div.select("p")
                    if paragraphs and len(paragraphs) > 1:  # Ensure we have meaningful content
                        content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
                        break
            
            # If still no content, try to get any text from the page
            if not content:
                # Look for the main content area
                main_content = soup.select_one("main") or soup.select_one("article") or soup.select_one("div.article")
                if main_content:
                    # Get all text nodes that are substantial
                    content_elements = []
                    for elem in main_content.find_all(['p', 'h2', 'h3', 'li']):
                        text = elem.text.strip()
                        if text and len(text) > 30:  # Only include substantial text
                            content_elements.append(text)
                    
                    if content_elements:
                        content = " ".join(content_elements)
            
            # If we still don't have content, use a generic message
            if not content:
                content = f"This article from Eurogamer discusses {title}. Visit {url} to read the full article."
            
            # Validate title and image_url before returning
            if not is_valid_title(title) or not is_valid_image_url(image_url):
                print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
                return None
                
            return create_article_object(title, image_url, content, url, self.name)
            
        except Exception as e:
            import traceback
            print(f"Error scraping article from Eurogamer at {url}: {e}")
            traceback.print_exc()
            return None
