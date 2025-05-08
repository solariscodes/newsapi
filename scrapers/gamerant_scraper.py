import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class GameRantScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://gamerant.com", "GameRant")
    
    def get_article_urls(self, limit=10):
        # Try different paths to find articles
        paths = ["/gaming", "/", "/news", "/game-news"]
        
        article_links = []
        
        for path in paths:
            try:
                print(f"Trying to access GameRant at {self.base_url}{path}")
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
                    "article.browse-clip",
                    "article",
                    "div.article-card",
                    "div.card",
                    "a[href*='/game-']",
                    "a[href*='/gaming/']",
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
                    # If limit is None, get all articles, otherwise respect the limit
            if limit is not None and len(article_links) >= limit:
                        break
                    
                    # If the article itself is an <a> tag
                    if article.name == 'a' and article.get("href"):
                        url = article.get("href")
                        if not url.startswith("http"):
                            url = self.base_url + url
                        if url not in article_links:
                            article_links.append(url)
                        continue
                    
                    # Try different selectors for links
                    for link_selector in ["a.bc-title-link", "a.title", "a[class*='title']", "a"]:
                        link_tag = article.select_one(link_selector)
                        if link_tag and link_tag.get("href"):
                            url = link_tag["href"]
                            if not url.startswith("http"):
                                url = self.base_url + url
                            if url not in article_links:
                                article_links.append(url)
                            break
                
                if article_links:
                    break  # If we found articles, no need to try other paths
            
            except Exception as e:
                print(f"Error accessing GameRant at {self.base_url}{path}: {e}")
                continue
        
        # If we still couldn't find any articles, try some hardcoded recent URLs
        if not article_links:
            print("Falling back to hardcoded GameRant URLs")
            fallback_urls = [
                "https://gamerant.com/best-rpgs-2024/",
                "https://gamerant.com/xbox-price-increase-2024/",
                "https://gamerant.com/nintendo-switch-2-games-price-increase/",
                "https://gamerant.com/elden-ring-shadow-of-the-erdtree-dlc-release-date-trailer/",
                "https://gamerant.com/call-of-duty-black-ops-6-release-date-trailer/"
            ]
            article_links = fallback_urls[:limit]
        
        return article_links[:limit]# If limit is None, return all articles, otherwise respect the limit
        return article_links if limit is None else article_links[:limit]
    
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
            
            # Extract title - try multiple selectors with improved approach
            title = ""
            
            # First try to get the title from meta tags (most reliable)
            meta_title = soup.select_one('meta[property="og:title"]') or soup.select_one('meta[name="twitter:title"]')
            if meta_title and meta_title.get('content'):
                title = meta_title.get('content').strip()
            
            # If no meta title, try standard HTML title selectors
            if not title or title.lower() == "game rant" or title.lower() == "gamerant":
                for title_selector in ["h1.title", "h1.entry-title", "h1.article-title", "h1", "header h1", ".article-title"]:
                    title_tag = soup.select_one(title_selector)
                    if title_tag:
                        potential_title = title_tag.text.strip()
                        if potential_title and potential_title.lower() != "game rant" and potential_title.lower() != "gamerant":
                            title = potential_title
                            break
            
            # If we still couldn't find a title, extract it from the URL as a fallback
            if not title or title.lower() == "game rant" or title.lower() == "gamerant":
                import re
                # Extract the last part of the URL and convert hyphens to spaces
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
                    
            # Make sure we don't just return the site name
            if not title or title.lower() == "game rant" or title.lower() == "gamerant":
                # Use the URL to create a meaningful title
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Extract image - try multiple selectors with better prioritization
            image_url = ""
            
            # First try to get the image from meta tags (most reliable)
            meta_image = soup.select_one('meta[property="og:image"]') or soup.select_one('meta[name="twitter:image"]')
            if meta_image and meta_image.get('content'):
                potential_url = meta_image.get('content')
                if potential_url and not (".svg" in potential_url.lower() or "logo" in potential_url.lower()):
                    if not ("author" in potential_url.lower() or "bio" in potential_url.lower() or "w=90" in potential_url.lower()):
                        image_url = potential_url
            
            # If no meta image, try to get the main article image
            main_image_selectors = [
                "div.header-img img", 
                "figure.wp-block-image img", 
                "div.featured-image img",
                "img.wp-post-image", 
                "picture img", 
                "div.article-featured-image img",
                "div.article-img img",
                "div.article-header img",
                "div.article-hero img",
                "div.entry-image img",
                # GameRant specific selectors
                "div.browse-clip-img img",
                "div.image-wrapper img",
                "div.lead-image img",
                "div.lead-img img"
            ]
            
            if not image_url:
                for img_selector in main_image_selectors:
                    image_tag = soup.select_one(img_selector)
                    if image_tag:
                        image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                        # Skip SVG, logos, and small author images
                        if image_url and not (".svg" in image_url.lower() or "logo" in image_url.lower()):
                            # Skip small author images that often contain "author" or "bio" in the URL
                            if not ("author" in image_url.lower() or "bio" in image_url.lower() or "w=90" in image_url.lower()):
                                break
            
            # If still no image, try to find the first substantial image in the article content
            if not image_url or ".svg" in image_url.lower() or "logo" in image_url.lower():
                content_div = soup.select_one("div.article-body") or soup.select_one("div.entry-content") or soup.select_one("article")
                if content_div:
                    for img in content_div.select("img"):
                        potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                        # Skip SVG images, logos, and tiny icons
                        if potential_url and not (".svg" in potential_url.lower() or "logo" in potential_url.lower()):
                            image_url = potential_url
                            break
            
            # If still no image, try to find any substantial image on the page
            if not image_url or ".svg" in image_url.lower() or "logo" in image_url.lower():
                for img in soup.select("img"):
                    potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                    # Skip SVG images, logos, and tiny icons
                    if potential_url and not (".svg" in potential_url.lower() or "logo" in potential_url.lower()):
                        # Check if it's a substantial image (not a tiny icon)
                        if "wp-content/uploads" in potential_url or "gamerantimages" in potential_url:
                            image_url = potential_url
                            break
            
            # Extract content - try multiple selectors
            content = ""
            for content_selector in ["div.article-body", "div.entry-content", "div.content-area", 
                                    "article", "div[class*='article'] div[class*='content']"]:
                content_div = soup.select_one(content_selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.select("div.related-article, div.affiliate-disclaimer, div.newsletter, div.comments, div.tags, div.social, nav, aside, script, style"):
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
                main_content = soup.select_one("main") or soup.select_one("article") or soup.select_one("div.content")
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
                content = f"This article from GameRant discusses {title}. Visit {url} to read the full article."
            
            # Validate title and image_url before returning
            if not is_valid_title(title) or not is_valid_image_url(image_url):
                print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
                return None
                
            return create_article_object(title, image_url, content, url, self.name)
            
        except Exception as e:
            import traceback
            print(f"Error scraping article from GameRant at {url}: {e}")
            traceback.print_exc()
            return None
