import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class EngadgetScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.engadget.com", "Engadget")
    
    def get_article_urls(self, limit=10):
        # Try different paths to find articles
        paths = ["/gaming", "/games", "/news", "/", "/tag/gaming"]
        
        article_links = []
        
        for path in paths:
            try:
                print(f"Trying to access Engadget at {self.base_url}{path}")
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
                    "div.o-hit",
                    "article",
                    "div.article",
                    "div.post",
                    "div.c-entry",
                    "div.card"
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
                    for link_selector in ["a.o-hit__link", "h2 a", "h3 a", "a.article-link", "a[href*='/20']", "a"]:
                        link_tag = article.select_one(link_selector)
                        if link_tag and link_tag.get("href"):
                            url = link_tag["href"]
                            if not url.startswith("http"):
                                url = self.base_url + url
                            if url not in article_links and "/tag/" not in url and "/author/" not in url:  # Avoid duplicates and tag/author pages
                                article_links.append(url)
                            break
                
                if article_links:
                    break  # If we found articles, no need to try other paths
            
            except Exception as e:
                print(f"Error accessing Engadget at {self.base_url}{path}: {e}")
                continue
        
        # If we still couldn't find any articles, try some hardcoded recent URLs
        if not article_links:
            print("Falling back to hardcoded Engadget URLs")
            fallback_urls = [
                "https://www.engadget.com/gaming/epic-games-takes-aim-at-apple-and-steam-with-zero-commission-policy-for-developers-183956940.html",
                "https://www.engadget.com/gaming/nintendo/nintendo-switch-2-pre-orders-latest-updates-console-remains-sold-out-at-gamestop-walmart-target-best-buy-and-others-140931858.html",
                "https://www.engadget.com/gaming/microsoft-is-raising-prices-on-the-xbox-series-s-and-series-x-132004594.html",
                "https://www.engadget.com/gaming/call-of-duty-black-ops-6-release-date-trailer-142538921.html",
                "https://www.engadget.com/gaming/elden-ring-shadow-of-the-erdtree-release-date-trailer-164512834.html"
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
            for title_selector in ["h1.t-h4", "h1.article-title", "h1.entry-title", "h1"]:
                title_tag = soup.select_one(title_selector)
                if title_tag:
                    title = title_tag.text.strip()
                    break
            
            # If we couldn't find a title, extract it from the URL as a fallback
            if not title:
                # Extract the last part of the URL and convert hyphens to spaces
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('.html', '').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Extract image - try multiple selectors
            image_url = ""
            for img_selector in ["div.t-article-image img", "div.article-image img", "div.featured-image img", 
                                "img.wp-post-image", "picture img", "div.article-image-wrapper img", 
                                "img.c-picture__image", "meta[property='og:image']"]:
                image_tag = soup.select_one(img_selector)
                if image_tag:
                    if img_selector == "meta[property='og:image']":
                        image_url = image_tag.get("content", "")
                    else:
                        image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                    
                    # Ensure URL is absolute
                    if image_url and not image_url.startswith(('http://', 'https://')):
                        if image_url.startswith('/'):
                            image_url = f"https://www.engadget.com{image_url}"
                        else:
                            image_url = f"https://www.engadget.com/{image_url}"
                    
                    if image_url:
                        break
            
            # If still no image, try to find any image in the article
            if not image_url:
                for img in soup.select("img"):
                    potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                    if potential_url and ("engadget" in potential_url or ".jpg" in potential_url or ".png" in potential_url):
                        # Ensure URL is absolute
                        if not potential_url.startswith(('http://', 'https://')):
                            if potential_url.startswith('/'):
                                potential_url = f"https://www.engadget.com{potential_url}"
                            else:
                                potential_url = f"https://www.engadget.com/{potential_url}"
                        image_url = potential_url
                        break
                        
            # If still no image, try to use a default image
            if not image_url or image_url.startswith('/_td_api/beacon/'):
                image_url = "https://s.yimg.com/os/creatr-uploaded-images/2020-10/fe92d4b0-0f9c-11eb-bfce-a5570d2300c0"  # Engadget logo
            
            # Extract content - try multiple selectors
            content = ""
            for content_selector in ["div.t-article-content", "div.article-content", "div.entry-content", 
                                    "article", "div.content"]:
                content_div = soup.select_one(content_selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.select("div.t-d-module, div.t-galleria, div.related-posts, div.newsletter, div.comments, div.social, nav, script, style"):
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
                content = f"This article from Engadget discusses {title}. Visit {url} to read the full article."
            
            # Validate title and image_url before returning
            if not is_valid_title(title) or not is_valid_image_url(image_url):
                print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
                return None
                
            return create_article_object(title, image_url, content, url, self.name)
            
        except Exception as e:
            import traceback
            print(f"Error scraping article from Engadget at {url}: {e}")
            traceback.print_exc()
            return None
