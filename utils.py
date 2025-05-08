import os
import json
import requests
import uuid
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

def get_soup(url, headers=None):
    """
    Fetch a webpage and return a BeautifulSoup object
    """
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.get(url, headers=default_headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_to_json(data, filename="gaming_news.json"):
    """
    Save scraped data to a JSON file, appending new articles without duplicates
    """
    # Create a timestamp for the scrape
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    existing_data = []
    existing_urls = set()
    
    # Try to load existing data if file exists
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_json = json.load(f)
                if "articles" in existing_json and isinstance(existing_json["articles"], list):
                    existing_data = existing_json["articles"]
                    # Create a set of existing URLs for quick lookup
                    existing_urls = {article["source_url"] for article in existing_data if "source_url" in article}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not read existing JSON file: {e}")
            # If file is corrupted, we'll start fresh
            existing_data = []
            existing_urls = set()
    
    # Filter out duplicates from new data
    new_articles = []
    for article in data:
        if article["source_url"] not in existing_urls:
            new_articles.append(article)
            existing_urls.add(article["source_url"])
    
    # Combine existing and new articles
    combined_articles = existing_data + new_articles
    
    # Prepare the data structure
    output = {
        "scrape_timestamp": timestamp,
        "article_count": len(combined_articles),
        "articles": combined_articles
    }
    
    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Use ensure_ascii=False to preserve Unicode characters
            # Use default escaping for special characters
            json.dump(output, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving JSON: {e}")
        # Fallback: Try to save with more aggressive encoding settings
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=True, indent=4)
    
    print(f"Saved {len(combined_articles)} articles to {filename} ({len(new_articles)} new articles added)")
    return len(new_articles)

def clean_text(text):
    """
    Clean and normalize text content, ensuring it's properly escaped for JSON
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    text = text.strip()
    
    # Escape special characters that might cause JSON issues
    # Note: json.dumps will handle most escaping, but we can do additional processing if needed
    # This is just for extra safety as json.dump with ensure_ascii=False should handle most cases
    text = text.replace('\\', '\\\\')
    
    return text


def is_valid_title(title):
    """
    Returns True if the title is non-empty and not a generic placeholder.
    """
    if not title or not isinstance(title, str):
        return False
    cleaned = title.strip().lower()
    if cleaned in ("", "untitled", "no title", "none", "null", "thegamer", "the gamer"):
        return False
    return True


def is_valid_image_url(url):
    """
    Returns True if the image URL is a valid HTTP(S) URL and not a data URI, base64, SVG, or empty.
    """
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if url == "":
        return False
    lowered = url.lower()
    if lowered.startswith("data:image/") or lowered.startswith("data:"):
        return False
    if "base64" in lowered:
        return False
    if lowered.endswith(".svg"):
        return False
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        return False
    return True

def extract_domain(url):
    """
    Extract the domain name from a URL
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def download_image(image_url, source_name, article_title, article_id=None):
    """
    Download an image from a URL and save it to a local directory
    Returns the local path to the saved image
    
    Parameters:
    - image_url: URL of the image to download
    - source_name: Name of the source website
    - article_title: Title of the article
    - article_id: Unique ID of the article (if provided, will be used for the filename)
    """
    if not image_url:
        return ""
    
    # Validate the URL - must start with http or https
    if not image_url.startswith(('http://', 'https://')):
        print(f"Invalid image URL: {image_url}")
        return find_fallback_image(source_name, article_title, article_id)
    
    # Strip URL parameters (everything after the question mark) to get the original image
    if '?' in image_url:
        print(f"Stripping URL parameters from: {image_url}")
        image_url = image_url.split('?')[0]
        print(f"Clean image URL: {image_url}")
    
    # Reject SVG files, logos, and other non-raster formats by checking URL
    parsed_url = urlparse(image_url)
    path = parsed_url.path.lower()
    url_lower = image_url.lower()
    
    # Check for SVG files
    if path.endswith('.svg') or '.svg?' in path or 'svg' in url_lower:
        print(f"Skipping SVG image: {image_url}")
        return find_fallback_image(source_name, article_title, article_id)
    
    # Check for logo images, especially for GameRant
    if 'logo' in url_lower or 'icon' in url_lower:
        print(f"Skipping logo image: {image_url}")
        return find_fallback_image(source_name, article_title, article_id)
    
    # Special case for GameRant SVG logo
    if source_name == "GameRant" and "gamerantimages.com/assets/images/gr-logo" in url_lower:
        print(f"Skipping GameRant logo: {image_url}")
        return find_fallback_image(source_name, article_title, article_id)
    
    # Create images directory if it doesn't exist
    images_dir = os.path.join(os.getcwd(), "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # Get file extension from URL or default to .jpg
    extension = os.path.splitext(path)[1].lower()
    if not extension or len(extension) > 5 or extension not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        extension = ".jpg"
    
    # Use the provided article_id if available, otherwise generate a new one
    if article_id:
        filename = f"{article_id}{extension}"
    else:
        # Create a unique filename using UUID and date if no article_id provided
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for brevity
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{timestamp}_{unique_id}{extension}"
    filepath = os.path.join(images_dir, filename)
    
    try:
        # Download the image
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Check if the content is an image and not SVG
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/') or content_type == 'image/svg+xml':
            print(f"Content is not a supported image format: {content_type} for URL {image_url}")
            return find_fallback_image(source_name, article_title)
        
        # Additional check: read first few bytes to verify it's an image file
        first_bytes = next(response.iter_content(256))
        # Check for common image file signatures
        is_image = False
        # JPEG signature
        if first_bytes.startswith(b'\xff\xd8'):
            is_image = True
        # PNG signature
        elif first_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            is_image = True
        # GIF signature
        elif first_bytes.startswith((b'GIF87a', b'GIF89a')):
            is_image = True
        # WEBP signature (usually starts with RIFF....WEBP)
        elif b'WEBP' in first_bytes[:20]:
            is_image = True
            
        if not is_image:
            print(f"File does not appear to be a valid image: {image_url}")
            return find_fallback_image(source_name, article_title)
        
        # Check if the image is too small (likely an icon or logo)
        img_size = int(response.headers.get('Content-Length', 0))
        if img_size < 5000:  # Less than 5KB is probably too small
            print(f"Image is too small ({img_size} bytes): {image_url}")
            # Try to find a fallback image based on the article title
            print(f"Searching for fallback image: {source_name} {article_title} gaming news")
            return find_fallback_image(source_name, article_title)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(first_bytes)  # Write the first chunk we already read
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Return the GitHub-friendly path to the image (using forward slashes)
        # This will work correctly when hosted on GitHub
        github_path = f"images/{filename}"
        return github_path
    
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return find_fallback_image(source_name, article_title, article_id)


def find_fallback_image(source_name, article_title, article_id=None):
    """
    Find a fallback image when the original image URL is not suitable
    Uses Google Image Search to find a relevant image based on the article title
    
    Parameters:
    - source_name: Name of the source website
    - article_title: Title of the article
    - article_id: Unique ID of the article (if provided, will be used for the filename)
    """
    # Create a search query based on the article title and source name
    search_query = f"{article_title} {source_name} gaming news"
    
    # Use a predefined list of fallback images for gaming news
    fallback_images = [
        "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/06/elder-scrolls-6-release-date-trailer-gameplay-setting-news.jpg",
        "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2023/01/best-games-2023.jpg",
        "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/12/most-anticipated-games-2023.jpg",
        "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/06/ps5-games-coming-soon.jpg",
        "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/09/xbox-series-x-games-coming-soon.jpg",
        "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/12/nintendo-switch-games-coming-soon.jpg",
        "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/08/pc-games-coming-soon.jpg",
        "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/best-gaming-news-sites.jpg"
    ]
    
    # Try to find a source-specific image first
    source_specific_images = {
        "IGN": "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/ign-logo.jpg",
        "GameSpot": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/07/gamespot-logo.jpg",
        "PCGamer": "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/pc-gamer-logo.jpg",
        "Eurogamer": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/07/eurogamer-logo.jpg",
        "Polygon": "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/polygon-logo.jpg",
        "Kotaku": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/07/kotaku-logo.jpg",
        "GameRant": "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/gamerant-logo.jpg",
        "TheGamer": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/07/thegamer-logo.jpg",
        "WCCFTech": "https://static1.thegamerimages.com/wordpress/wp-content/uploads/2022/07/wccftech-logo.jpg",
        "Engadget": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/07/engadget-logo.jpg"
    }
    
    # Try to get a source-specific image
    if source_name in source_specific_images:
        fallback_url = source_specific_images[source_name]
        local_path = download_fallback_image(fallback_url, source_name, article_id)
        if local_path:
            return local_path
    
    # If source-specific image fails, try a random gaming image
    import random
    random.shuffle(fallback_images)  # Randomize the order
    
    for fallback_url in fallback_images:
        local_path = download_fallback_image(fallback_url, source_name, article_id)
        if local_path:
            return local_path
    
    # If all fallbacks fail, return empty string
    return ""


def download_fallback_image(image_url, source_name, article_id=None):
    """
    Download a fallback image and save it
    Similar to download_image but simplified for fallbacks
    
    Parameters:
    - image_url: URL of the fallback image
    - source_name: Name of the source website
    - article_id: Unique ID of the article (if provided, will be used for the filename)
    """
    try:
        # Create images directory if it doesn't exist
        images_dir = os.path.join(os.getcwd(), "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # Use the provided article_id if available, otherwise generate a new one
        if article_id:
            filename = f"{article_id}.jpg"
        else:
            # Create a unique filename if no article_id provided
            unique_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{timestamp}_{unique_id}_fallback.jpg"
            
        filepath = os.path.join(images_dir, filename)
        
        # Download the image
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Return the GitHub-friendly path
        return f"images/{filename}"
        
    except Exception as e:
        print(f"Error downloading fallback image: {e}")
        return ""

def save_content_to_txt(article_id, content):
    """
    Save article content to a TXT file in the 'content' directory
    """
    # Create content directory if it doesn't exist
    content_dir = os.path.join(os.getcwd(), "content")
    if not os.path.exists(content_dir):
        os.makedirs(content_dir)
    
    # Create filename using article ID
    filename = f"{article_id}.txt"
    file_path = os.path.join(content_dir, filename)
    
    # Save content to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"content/{filename}"
    except Exception as e:
        print(f"Error saving content to TXT file: {e}")
        return ""

def create_article_object(title, image_url, content, source_url, source_name=None):
    """
    Create a standardized article object with GitHub-compatible paths and unique ID
    """
    # Clean the title and content
    cleaned_title = clean_text(title)
    
    # Special handling for content to ensure it doesn't break JSON
    if content and content.strip():
        # First do basic cleaning
        cleaned_content = clean_text(content)
        
        # Additional safety check for problematic characters
        try:
            # Test if the content can be properly serialized to JSON
            import json
            json.dumps({"test": cleaned_content})
        except Exception as e:
            # If there's an error, apply more aggressive cleaning
            print(f"Warning: Content contains characters that could break JSON: {e}")
            # Remove or replace problematic characters
            import re
            cleaned_content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', cleaned_content)
    else:
        # If content is empty, create a default message based on the title and source
        if 'video' in source_url.lower() or any(video_site in source_url.lower() for video_site in ['youtube', 'vimeo', 'ign.com/videos']):
            # Special handling for video content
            cleaned_content = f"{cleaned_title}\n\nThis is a video article from {source_name}. Please visit the source URL to watch the video content.\n\nSource: {source_url}"
        else:
            # Default message for other empty content
            cleaned_content = f"No text content available for this article. Please visit the original source for more information.\n\nSource: {source_url}"
    
    if not source_name:
        source_name = extract_domain(source_url)
    
    # Generate a unique ID for the article
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for brevity
    article_id = f"{timestamp}_{unique_id}"
    
    # Save content to TXT file and get the path
    content_file_path = save_content_to_txt(article_id, cleaned_content)
    
    # Download the image with the article ID
    local_image_path = download_image(image_url, source_name, cleaned_title, article_id)
    
    # Create GitHub repo URL for the image
    github_image_url = ""
    if local_image_path:
        # Format: https://raw.githubusercontent.com/username/repo/branch/path
        github_image_url = f"https://raw.githubusercontent.com/solariscodes/newsrepo/master/{local_image_path}"
    
    # Create GitHub repo URL for the content file
    github_content_url = ""
    if content_file_path:
        github_content_url = f"https://raw.githubusercontent.com/solariscodes/newsrepo/master/{content_file_path}"
    
    return {
        "id": article_id,
        "title": cleaned_title,
        "image_url": image_url,
        "local_image_path": local_image_path,
        "github_image_url": github_image_url,
        "content_file_path": content_file_path,
        "github_content_url": github_content_url,
        "source_url": source_url,
        "source_name": source_name,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
