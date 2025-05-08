import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_soup, create_article_object, clean_text, is_valid_title, is_valid_image_url
from scrapers.base_scraper import BaseScraper

class TheGamerScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://www.thegamer.com", "TheGamer")
    
    def get_article_urls(self, limit=10):
        # Try different paths to find articles
        paths = ["/category/game-news", "/gaming", "/games", "/news", "/"]
        
        article_links = []
        
        for path in paths:
            try:
                print(f"Trying to access TheGamer at {self.base_url}{path}")
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
                    "article.list-item",
                    "article",
                    "div.article",
                    "div.post",
                    "div.entry",
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
                    # If limit is None, get all articles, otherwise respect the limit
            if limit is not None and len(article_links) >= limit:
                        break
                    
                    # Try different selectors for links
                    for link_selector in ["a.article-link", "h2 a", "h3 a", "a.title", "a[href*='/20']", "a"]:
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
                print(f"Error accessing TheGamer at {self.base_url}{path}: {e}")
                continue
        
        # If we still couldn't find any articles, try some hardcoded recent URLs
        if not article_links:
            print("Falling back to hardcoded TheGamer URLs")
            fallback_urls = [
                "https://www.thegamer.com/elden-ring-shadow-of-the-erdtree-release-date-trailer/",
                "https://www.thegamer.com/gta-6-release-date-trailer/",
                "https://www.thegamer.com/call-of-duty-black-ops-6-release-date-trailer/",
                "https://www.thegamer.com/nintendo-switch-2-release-date-news/",
                "https://www.thegamer.com/xbox-series-x-price-increase/"
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
            
            # Extract title - comprehensive approach to ensure we never return just "TheGamer"
            title = ""
            
            # First try to get the title from meta tags (most reliable)
            meta_title = soup.select_one('meta[property="og:title"]') or soup.select_one('meta[name="twitter:title"]')
            if meta_title and meta_title.get('content'):
                potential_title = meta_title.get('content').strip()
                if potential_title and potential_title.lower() != "thegamer" and potential_title.lower() != "the gamer":
                    title = potential_title
            
            # If no meta title, try HTML title tag
            if not title or title.lower() == "thegamer" or title.lower() == "the gamer":
                title_tag = soup.select_one('title')
                if title_tag:
                    potential_title = title_tag.text.strip()
                    # Remove site name from title if it's in the format "Article Title - TheGamer"
                    if ' - ' in potential_title:
                        potential_title = potential_title.split(' - ')[0].strip()
                    if potential_title and potential_title.lower() != "thegamer" and potential_title.lower() != "the gamer":
                        title = potential_title
            
            # Try standard HTML heading selectors
            if not title or title.lower() == "thegamer" or title.lower() == "the gamer":
                for title_selector in ["h1.title", "h1.article-title", "h1.entry-title", "h1", "header h1", ".article-title", ".post-title", "article h1"]:
                    title_tag = soup.select_one(title_selector)
                    if title_tag:
                        potential_title = title_tag.text.strip()
                        if potential_title and potential_title.lower() != "thegamer" and potential_title.lower() != "the gamer":
                            title = potential_title
                            break
            
            # Try to extract from JSON-LD structured data
            if not title or title.lower() == "thegamer" or title.lower() == "the gamer":
                for script in soup.select('script[type="application/ld+json"]'):
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'headline' in data:
                            potential_title = data['headline']
                            if potential_title and potential_title.lower() != "thegamer" and potential_title.lower() != "the gamer":
                                title = potential_title
                                break
                    except:
                        continue
            
            # If we still couldn't find a title, extract it from the URL as a fallback
            if not title or title.lower() == "thegamer" or title.lower() == "the gamer":
                # Extract the last part of the URL and convert hyphens to spaces
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Final check - never return just the site name
            if not title or title.lower() == "thegamer" or title.lower() == "the gamer":
                # Use the URL to create a meaningful title
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
                    
            # Add a prefix if the title was generated from URL
            if title and url and title.lower() in url.lower().replace('-', ' '):
                print(f"Generated title from URL: {title}")
            
            # Final validation - if we somehow still have TheGamer as the title, force a URL-based title
            if title.lower() == "thegamer" or title.lower() == "the gamer":
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    title = ' '.join(word.capitalize() for word in title_from_url.split())
            
            # Extract image - try multiple selectors
            image_url = ""
            for img_selector in ["div.image-holder img", "figure.wp-block-image img", "div.featured-image img", 
                                "img.wp-post-image", "picture img", "div.article-image img",
                                "meta[property='og:image']", "div.post-thumbnail img", "img.attachment-large"]:
                image_tag = soup.select_one(img_selector)
                if image_tag:
                    if img_selector == "meta[property='og:image']":
                        image_url = image_tag.get("content", "")
                    else:
                        image_url = image_tag.get("data-src") or image_tag.get("data-lazy-src") or image_tag.get("src", "")
                    if image_url:
                        # Skip SVG logo images
                        if ".svg" in image_url.lower() or "logo" in image_url.lower():
                            image_url = ""
                            continue
                        break
            
            # If still no image, try to find any image in the article
            if not image_url:
                for img in soup.select("img"):
                    potential_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                    if potential_url and (".jpg" in potential_url or ".png" in potential_url or ".webp" in potential_url):
                        # Skip SVG logo images
                        if ".svg" in potential_url.lower() or "logo" in potential_url.lower():
                            continue
                        image_url = potential_url
                        break
            
            # If still no image, use a default image
            if not image_url or ".svg" in image_url.lower():
                image_url = "https://static0.thegamerimages.com/wordpress/wp-content/uploads/2023/05/thegamer-default-og-1.jpg"  # Default image for TheGamer
            
            # Extract content - try multiple selectors
            content = ""
            for content_selector in ["div.article-body", "div.entry-content", "div.article-content", 
                                    "article", "div.content"]:
                content_div = soup.select_one(content_selector)
                if content_div:
                    # Remove unwanted elements
                    for unwanted in content_div.select("div.related-article, div.ad-unit, div.newsletter, div.comments, div.social, nav, script, style"):
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
                content = f"This article from TheGamer discusses {title}. Visit {url} to read the full article."
            
            # Validate title and image_url before returning
            if not is_valid_title(title) or not is_valid_image_url(image_url):
                print(f"Skipping invalid article from {self.name}: {url} - Invalid title or image")
                return None
                
            return create_article_object(title, image_url, content, url, self.name)
            
        except Exception as e:
            import traceback
            print(f"Error scraping article from TheGamer at {url}: {e}")
            traceback.print_exc()
            return None
