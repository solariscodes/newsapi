#!/usr/bin/env python3
import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import NewsDatabase
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import logging
from collections import OrderedDict
from fallback_data import get_fallback_articles, save_fallback_data

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.json.sort_keys = False  # Prevent Flask from reordering JSON keys
CORS(app)  # Enable CORS for all routes

# Initialize database
db = NewsDatabase()

# Function to run the scraper
def run_scraper():
    logger.info("Starting scheduled scraping job")
    try:
        # Import the scraper modules directly
        from scraper import clear_data
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
        
        logger.info("Scraping directly from app.py")
        
        # Initialize scrapers
        scrapers = {
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
        
        # Scrape articles (get as many as possible from each source)
        all_articles = []
        for name, scraper in scrapers.items():
            try:
                logger.info(f"Scraping from {name}")
                articles = scraper.scrape(limit=None)  # No limit - get ALL articles from each source
                if articles:
                    all_articles.extend(articles)
                    logger.info(f"Got {len(articles)} articles from {name}")
            except Exception as e:
                logger.error(f"Error scraping {name}: {str(e)}")
        
        # Add articles to database
        if all_articles:
            # Add to database
            new_count = db.add_articles(all_articles)
            logger.info(f"Added {new_count} new articles to database")
            
            # Export to JSON
            article_count = db.export_to_json()
            logger.info(f"Exported {article_count} articles to JSON")
        else:
            logger.error("No articles were scraped. Checking if database already has articles")
            
            # Check if database already has articles
            existing_count = db.get_article_count()
            if existing_count > 0:
                logger.info(f"Database already has {existing_count} articles, skipping fallback data")
            else:
                logger.warning("Database is empty, using fallback data as last resort")
                # Use fallback data only if database is empty
                fallback_articles = get_fallback_articles()
                new_count = db.add_articles(fallback_articles)
                logger.info(f"Added {new_count} fallback articles to database")
                
                # Export fallback data to JSON
                article_count = db.export_to_json()
                logger.info(f"Exported {article_count} fallback articles to JSON")
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_scraper, 'interval', hours=3)  # Run every 3 hours

# Run scraper on startup to ensure we have fresh articles
run_scraper()

# API Routes
@app.route('/')
def index():
    """API documentation"""
    endpoints = {
        "endpoints": {
            "GET /": "API documentation",
            "GET /articles": "Get all articles with pagination",
            "GET /articles/<article_id>": "Get a specific article by ID",
            "GET /articles/sources": "Get list of available news sources",
            "GET /articles/search?q=<query>": "Search articles by keyword",
            "GET /json": "Get the entire dataset as a static JSON file"
        }
    }
    return jsonify(endpoints)

@app.route('/articles')
def get_articles():
    """Get all articles with optional pagination and filtering"""
    # Parse query parameters
    limit = request.args.get('limit', default=100, type=int)  # Default to 100 articles
    offset = request.args.get('offset', default=0, type=int)
    source = request.args.get('source', default=None, type=str)
    
    # Get articles from database
    articles = db.get_all_articles(limit=limit, offset=offset, source=source)
    total_count = db.get_article_count(source=source)
    
    # If no articles found, use fallback data as last resort
    if not articles:
        logger.warning("No articles in database, using fallback data as last resort")
        articles = get_fallback_articles()
        total_count = len(articles)
        
        # Try to add fallback articles to database in a background thread to avoid blocking
        def add_fallback_articles_background():
            try:
                db.add_articles(articles)
                db.export_to_json()
            except Exception as e:
                logger.error(f"Failed to add fallback articles to database: {str(e)}")
        
        import threading
        background_thread = threading.Thread(target=add_fallback_articles_background)
        background_thread.daemon = True
        background_thread.start()
    
    # Format articles to include only necessary fields in the proper order
    # Using list comprehension for better performance
    formatted_articles = [
        OrderedDict([
            ("id", article.get('id', '')),
            ("title", article.get('title', '')),
            ("content", article.get('content', '')),
            ("source_name", article.get('source_name', '')),
            ("source_url", article.get('source_url', '')),
            ("image_url", article.get('image_url', '')),
            ("local_image_path", article.get('local_image_path', '')),
            ("scrape_timestamp", article.get('scrape_timestamp', ''))
        ]) for article in articles
    ]
    
    # Return response with the formatted articles
    return jsonify({
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "articles": formatted_articles
    })

@app.route('/articles/<article_id>')
def get_article(article_id):
    """Get a specific article by ID"""
    article = db.get_article_by_id(article_id)
    if article:
        # Format article to include only necessary fields in the proper order
        formatted_article = OrderedDict([
            ("id", article.get('id', '')),
            ("title", article.get('title', '')),
            ("content", article.get('content', '')),
            ("source_name", article.get('source_name', '')),
            ("source_url", article.get('source_url', '')),
            ("image_url", article.get('image_url', '')),
            ("local_image_path", article.get('local_image_path', '')),
            ("scrape_timestamp", article.get('scrape_timestamp', ''))
        ])
        return jsonify(formatted_article)
    return jsonify({"error": "Article not found"}), 404

@app.route('/articles/sources')
def get_sources():
    """Get a list of all available news sources"""
    sources = db.get_article_sources()
    return jsonify({
        "count": len(sources),
        "sources": sources
    })

@app.route('/articles/search')
def search_articles():
    """Search for articles by keyword"""
    query = request.args.get('q', default='', type=str)
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
        
    articles = db.search_articles(query, limit=limit, offset=offset)
    
    # Format articles to include only necessary fields in the proper order
    formatted_articles = []
    for article in articles:
        formatted_article = OrderedDict([
            ("id", article.get('id', '')),
            ("title", article.get('title', '')),
            ("content", article.get('content', '')),
            ("source_name", article.get('source_name', '')),
            ("source_url", article.get('source_url', '')),
            ("image_url", article.get('image_url', '')),
            ("local_image_path", article.get('local_image_path', '')),
            ("scrape_timestamp", article.get('scrape_timestamp', ''))
        ])
        formatted_articles.append(formatted_article)
    
    return jsonify({
        "query": query,
        "count": len(formatted_articles),
        "articles": formatted_articles
    })

@app.route('/json')
def get_json():
    """Return the static JSON file with all articles"""
    # Ensure the JSON file exists by exporting if needed
    if not os.path.exists('gaming_news.json'):
        db.export_to_json()
    
    # Read and return the JSON file
    with open('gaming_news.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    # Create images directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')
    return send_from_directory('images', filename, as_attachment=False)

@app.route('/content/<path:filename>')
def serve_content(filename):
    """Serve content files from the content directory"""
    return send_from_directory('content', filename)

# Main entry point
if __name__ == "__main__":
    # Start the scheduler
    scheduler.start()
    
    # For Railway deployment: Always run a scrape on startup
    # This ensures fresh content on every deploy
    logger.info("Running scraper on startup (Railway deployment)")
    run_scraper()
    
    # Get the port from environment variable (for Railway deployment)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)
