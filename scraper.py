#!/usr/bin/env python3
import os
import sys
import json
import argparse
import threading
import queue
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import utility functions
from utils import save_to_json, download_image

# Import database module
from database import NewsDatabase

# Import scrapers
from scrapers.ign_scraper import IGNScraper
from scrapers.pcgamer_scraper import PCGamerScraper
from scrapers.gamespot_scraper import GameSpotScraper
from scrapers.eurogamer_scraper import EurogamerScraper
from scrapers.gamerant_scraper import GameRantScraper
from scrapers.polygon_scraper import PolygonScraper
from scrapers.kotaku_scraper import KotakuScraper
from scrapers.wccftech_scraper import WCCFTechScraper
from scrapers.thegamer_scraper import TheGamerScraper
from scrapers.engadget_scraper import EngadgetScraper

def clear_data(json_file, images_dir="images", content_dir="content"):
    """
    Clear existing JSON file, images directory, and content directory
    """
    # Create empty JSON structure
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    empty_data = {
        "scrape_timestamp": timestamp,
        "article_count": 0,
        "articles": []
    }
    
    # Save empty JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(empty_data, f, ensure_ascii=False, indent=4)
    
    # Clear images directory
    if os.path.exists(images_dir):
        for file in os.listdir(images_dir):
            file_path = os.path.join(images_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    
    # Clear content directory
    if os.path.exists(content_dir):
        for file in os.listdir(content_dir):
            file_path = os.path.join(content_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    
    print(f"Cleared existing data: {json_file}, {images_dir}/, and {content_dir}/")

def main():
    parser = argparse.ArgumentParser(description='Scrape gaming news articles from various websites')
    parser.add_argument('--limit', type=int, default=100, help='Number of articles to scrape from each website (default: 100)')
    parser.add_argument('--output', type=str, default='gaming_news.json', help='Output JSON file (default: gaming_news.json)')
    parser.add_argument('--sites', type=str, nargs='+', help='Specific sites to scrape (default: all sites)')
    parser.add_argument('--clear', action='store_true', help='Clear existing JSON file and images before scraping (default: False)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed debug information (default: False)')
    parser.add_argument('--db', action='store_true', help='Use SQLite database to store articles (default: False)')
    args = parser.parse_args()
    
    # Clear existing data if requested and exit
    if args.clear:
        clear_data(args.output)
        print("Data cleared successfully. Use the scraper without --clear to start scraping.")
        return
    
    # Initialize all scrapers
    all_scrapers = {
        'ign': IGNScraper(),
        'pcgamer': PCGamerScraper(),
        'gamespot': GameSpotScraper(),
        'eurogamer': EurogamerScraper(),
        'gamerant': GameRantScraper(),
        'polygon': PolygonScraper(),
        'kotaku': KotakuScraper(),
        'wccftech': WCCFTechScraper(),
        'thegamer': TheGamerScraper(),
        'engadget': EngadgetScraper()
    }
    
    # Determine which scrapers to use
    if args.sites:
        scrapers = {site: all_scrapers[site] for site in args.sites if site in all_scrapers}
        if not scrapers:
            print(f"Error: No valid sites specified. Available sites: {', '.join(all_scrapers.keys())}")
            sys.exit(1)
    else:
        scrapers = all_scrapers
    
    print(f"Starting to scrape {len(scrapers)} gaming news websites...")
    print(f"Articles per site: {args.limit}")
    
    # Scrape articles from each website using threads
    all_articles = []
    results_queue = queue.Queue()
    
    def scrape_site(name, scraper, limit):
        try:
            # No need to print starting message - will be shown in progress bar
            articles = scraper.scrape(limit)
            results_queue.put((name, articles))
            return name, len(articles)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] {name}: {e}")
            # Only print traceback in debug mode or if explicitly requested
            if '--verbose' in sys.argv:
                traceback.print_exc()
            results_queue.put((name, []))
            return name, 0
    
    print(f"Starting scraping with {len(scrapers)} sources...")
    
    # Create a progress bar for overall scraping progress
    progress_bar = tqdm(total=len(scrapers), desc="Overall progress", position=0)
    site_status = {name: "Pending" for name in scrapers.keys()}
    
    # Use ThreadPoolExecutor to run scrapers in parallel
    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        # Submit all scraping tasks
        future_to_site = {executor.submit(scrape_site, name, scraper, args.limit): name 
                         for name, scraper in scrapers.items()}
        
        # Process results as they complete
        for future in as_completed(future_to_site):
            site_name = future_to_site[future]
            try:
                name, count = future.result()
                site_status[name] = f"[OK] {count} articles"
                # Update progress bar description to show current status
                status_str = ", ".join([f"{site}: {status}" for site, status in site_status.items()])
                progress_bar.set_description(f"Progress: {status_str}")
                progress_bar.update(1)
            except Exception as e:
                site_status[site_name] = f"[FAILED]"
                progress_bar.update(1)
    
    progress_bar.close()
    
    # Collect all articles from the queue
    while not results_queue.empty():
        name, articles = results_queue.get()
        if articles:
            all_articles.extend(articles)
    
    # Post-process articles to fix any issues
    fixed_count = 0
    for article in all_articles:
        # Fix GameRant articles with missing or problematic images
        if article.get('source_name') == 'GameRant' and (not article.get('image_url') or 
                                                       'logo' in article.get('image_url', '').lower() or 
                                                       'svg' in article.get('image_url', '').lower() or
                                                       'author' in article.get('image_url', '').lower() or
                                                       'w=90' in article.get('image_url', '').lower()):
            fixed_count += 1
            if args.verbose:
                print(f"Fixing GameRant article image: {article.get('title')}")
            # Use a reliable gaming image as fallback
            article['image_url'] = "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2022/06/elder-scrolls-6-release-date-trailer-gameplay-setting-news.jpg"
            # Download the image and update the paths
            local_path = download_image(article['image_url'], 'GameRant', article.get('title', ''))
            if local_path:
                article['local_image_path'] = local_path
                article['github_image_url'] = f"https://raw.githubusercontent.com/solariscodes/newsrepo/master/{local_path}"
    
    if fixed_count > 0:
        print(f"Fixed {fixed_count} articles with problematic images")
        
        # Fix TheGamer articles with generic titles
        if article.get('source_name') == 'TheGamer' and (article.get('title') == 'TheGamer' or article.get('title') == 'The Gamer'):
            print(f"Fixing TheGamer article title for: {article.get('source_url')}")
            # Extract title from URL
            url = article.get('source_url', '')
            if url:
                # Get the last part of the URL (after the last slash)
                url_parts = url.rstrip('/').split('/')
                if url_parts:
                    title_from_url = url_parts[-1].replace('-', ' ').replace('/', ' ')
                    # Capitalize the first letter of each word
                    new_title = ' '.join(word.capitalize() for word in title_from_url.split())
                    article['title'] = new_title
                    print(f"  New title: {new_title}")
            else:
                # If no URL, use a generic title with content preview
                content = article.get('content', '')
                if content:
                    # Use first 50 characters of content as title
                    preview = content[:50].strip()
                    if len(content) > 50:
                        preview += '...'
                    article['title'] = f"TheGamer Article: {preview}"
                    print(f"  New title from content: {article['title']}")
                print(f"Updated GameRant article with new image: {local_path}")
    
    # Generate a summary of articles by source
    source_counts = {}
    for article in all_articles:
        source = article.get('source_name', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Save articles to database if --db flag is used, otherwise save to JSON
    if args.db:
        # Initialize database connection
        db = NewsDatabase()
        new_articles_count = db.add_articles(all_articles)
        
        # Also export to JSON for compatibility
        if args.output:
            db.export_to_json(args.output)
            print(f"Exported database to JSON: {args.output}")
    else:
        # Save articles to JSON using traditional method
        new_articles_count = save_to_json(all_articles, args.output)
    
    # Print a concise summary
    if all_articles:
        print("\n" + "=" * 50)
        print(f"SCRAPING SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print(f"Total articles: {len(all_articles)} ({new_articles_count} new)")
        print("Articles by source:")
        for source, count in sorted(source_counts.items()):
            print(f"  {source}: {count}")
        
        if args.db:
            print(f"Storage: SQLite database + JSON export ({args.output})")
        else:
            print(f"Storage: JSON file only ({args.output})")
        print("=" * 50)
    else:
        print("\nNo articles were scraped. Please check your internet connection or try again later.")

if __name__ == "__main__":
    main()
