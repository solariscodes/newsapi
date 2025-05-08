import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class WCCFTechScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://wccftech.com", "WCCFTech")
    
    def get_article_urls(self, limit=10):
        # Try different paths to find articles
        paths = ["/topic/games", "/", "/category/games", "/news"]
        
        article_links = []
        
        for path in paths:
            try:
                print(f"Trying to access WCCFTech at {self.base_url}{path}")
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
                    "article.post",
                    "article",
                    "div.post",
                    "div.article",
                    "div.news-item",
                    "div.entry"
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
                    
                    # Try different selectors for links
                    for link_selector in ["h2.entry-title a", "h2 a", "h3 a", "a.title", "a[href*='/20']"]:  
                        link_tag = article.select_one(link_selector)
                        if link_tag and link_tag.get("href"):
                            url = link_tag["href"]
                            if not url.startswith("http"):
                                url = self.base_url + url
                            if url not in article_links:  # Avoid duplicates
                                article_links.append(url)
                            break
                
                if article_links:
                    break  # If we found articles, no need to try other paths
            
            except Exception as e:
                print(f"Error accessing WCCFTech at {self.base_url}{path}: {e}")
                continue
        
        # If we still couldn't find any articles, try some hardcoded recent URLs
        if not article_links:
            print("Falling back to hardcoded WCCFTech URLs")
            fallback_urls = [
                "https://wccftech.com/xbox-price-increase-2024-series-x-s-games-accessories/",
                "https://wccftech.com/nintendo-switch-2-games-price-increase/",
                "https://wccftech.com/elden-ring-shadow-of-the-erdtree-release-date-trailer/",
                "https://wccftech.com/call-of-duty-black-ops-6-release-date-trailer/",
                "https://wccftech.com/gta-6-release-date-trailer/"
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
            for title_selector in ["h1.entry-title", "h1.title", "h1.post-title", "h1"]:
                title_tag = soup.select_one(title_selector)
                if title_tag:
                    title = title_tag.text.strip()
                    break
            
            # If we couldn't find a title, extract it from the URL as a fallback
            if not title:
                # Extract the last part of the URL and convert hyphens to spaces
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Extract image - try multiple selectors
            image_url = ""
            for img_selector in ["div.entry-content img", "div.featured-image img", "div.post-thumbnail img", 
                                "img.wp-post-image", "picture img", "div.featured img"]:
                image_tag = soup.select_one(img_selector)
                if image_tag:
                    image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                    if image_url:
                        break
            
            # If still no image, try to find any image in the article
            if not image_url:
                for img in soup.select("img"):
                    potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                    if potential_url and ("wccftech" in potential_url or "/wp-content/" in potential_url):
                        image_url = potential_url
                        break
            
            # Extract content - try multiple selectors
            content = ""
            for content_selector in ["div.entry-content", "div.post-content", "div.article-content", 
                                    "article", "div.content"]:
                content_div = soup.select_one(content_selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.select("div.code-block, div.wp-block-embed, div.related-posts, div.newsletter, div.comments, div.tags, div.social, nav, script, style"):
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
                main_content = soup.select_one("main") or soup.select_one("article") or soup.select_one("div.post")
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
                content = f"This article from WCCFTech discusses {title}. Visit {url} to read the full article."
            
            # Validate title and image_url before returning
            if not is_valid_title(title) or not is_valid_image_url(image_url):
                print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
                return None
                
            return create_article_object(title, image_url, content, url, self.name)
            
        except Exception as e:
            import traceback
            print(f"Error scraping article from WCCFTech at {url}: {e}")
            traceback.print_exc()
            return None
