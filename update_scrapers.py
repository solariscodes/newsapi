#!/usr/bin/env python3
"""
Script to update all scrapers to handle None as a limit properly.
This will modify all scraper files to ensure they can scrape unlimited articles.
"""
import os
import re

def update_scraper_file(file_path):
    """Update a scraper file to handle None as a limit properly"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the get_article_urls method with limit check
    pattern = r'(def get_article_urls\(self, limit=\d+\):.*?for .*?:.*?)if len\(.*?\) >= limit:(.*?return .*?\[:limit\])'
    replacement = r'\1# If limit is None, get all articles, otherwise respect the limit\n            if limit is not None and len(article_links) >= limit:\2# If limit is None, return all articles, otherwise respect the limit\n        return article_links if limit is None else article_links[:limit]'
    
    # Use re.DOTALL to make . match newlines
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Only write if changes were made
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated {file_path}")
    else:
        print(f"No changes needed for {file_path}")

def main():
    """Update all scraper files"""
    scrapers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scrapers')
    
    # Get all scraper files
    scraper_files = [
        os.path.join(scrapers_dir, f) 
        for f in os.listdir(scrapers_dir) 
        if f.endswith('_scraper.py') and f != 'base_scraper.py'
    ]
    
    # Update each scraper file
    for file_path in scraper_files:
        update_scraper_file(file_path)
    
    print(f"Updated {len(scraper_files)} scraper files")

if __name__ == "__main__":
    main()
