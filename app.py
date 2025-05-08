#!/usr/bin/env python3
import os
import json
import time
import sys
import traceback
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import NewsDatabase
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import logging
from collections import OrderedDict
from fallback_data import get_fallback_articles, save_fallback_data

# Configure logging - more verbose for Railway deployment
log_file = 'app.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
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
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Files in current directory: {os.listdir('.')}")
    logger.info(f"Environment: {'RAILWAY_ENVIRONMENT' in os.environ and 'Railway' or 'Local'}")
    
    # Check if we can access external sites
    try:
        test_response = requests.get("https://www.google.com", timeout=10)
        logger.info(f"Internet connectivity test: {test_response.status_code}")
    except Exception as e:
        logger.error(f"Internet connectivity test failed: {str(e)}")
    
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
        success_count = 0
        error_count = 0
        
        for name, scraper in scrapers.items():
            try:
                logger.info(f"Scraping from {name}")
                # Add a retry mechanism for Railway environment
                max_retries = 3
                retry_count = 0
                articles = []
                
                while retry_count < max_retries and not articles:
                    try:
                        # No limit on articles per source for Railway
                        is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
                        # Log the environment
                        logger.info(f"Scraping in {'Railway' if is_railway else 'Local'} environment")
                        limit = None  # Get all articles regardless of environment
                        articles = scraper.scrape(limit=limit)
                        if articles:
                            break
                    except Exception as retry_error:
                        logger.warning(f"Retry {retry_count+1}/{max_retries} for {name} failed: {str(retry_error)}")
                        retry_count += 1
                        time.sleep(2)  # Wait before retrying
                
                if articles:
                    all_articles.extend(articles)
                    logger.info(f"Got {len(articles)} articles from {name}")
                    success_count += 1
                else:
                    logger.error(f"Failed to get articles from {name} after {max_retries} retries")
                    error_count += 1
            except Exception as e:
                logger.error(f"Error scraping {name}: {str(e)}")
                logger.error(traceback.format_exc())
                error_count += 1
        
        logger.info(f"Scraping summary: {success_count} sources succeeded, {error_count} sources failed")
        
        # Add articles to database
        if all_articles:
            # Add to database
            new_count = db.add_articles(all_articles)
            logger.info(f"Added {new_count} new articles to database")
            
            # Export to JSON
            article_count = db.export_to_json()
            logger.info(f"Exported {article_count} articles to JSON")
            
            # Log database and file status
            logger.info(f"Database article count: {db.get_article_count()}")
            if os.path.exists('gaming_news.json'):
                logger.info(f"gaming_news.json size: {os.path.getsize('gaming_news.json')} bytes")
                with open('gaming_news.json', 'r') as f:
                    json_data = json.load(f)
                    logger.info(f"JSON article count: {json_data.get('article_count', 0)}")
            else:
                logger.warning("gaming_news.json does not exist")
        else:
            logger.error("No articles were scraped. Checking if database already has articles")
            
            # Check if database already has articles
            existing_count = db.get_article_count()
            if existing_count > 0:
                logger.info(f"Database already has {existing_count} articles, skipping fallback data")
                # Force export to JSON to ensure it's up to date
                article_count = db.export_to_json()
                logger.info(f"Re-exported {article_count} existing articles to JSON")
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
        logger.error(traceback.format_exc())

# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_scraper, 'interval', hours=3)  # Run every 3 hours

# Add a health check endpoint that also triggers scraping
@app.route('/health')
def health_check():
    """Health check endpoint that also triggers scraping if needed"""
    # Check if we have articles in the database
    article_count = db.get_article_count()
    logger.info(f"Health check: {article_count} articles in database")
    
    # If we have fewer than 20 articles, trigger a scrape
    if article_count < 20:
        logger.info("Health check: Not enough articles, triggering scrape")
        # Run in a background thread to avoid blocking the health check
        import threading
        scrape_thread = threading.Thread(target=run_scraper)
        scrape_thread.daemon = True
        scrape_thread.start()
    
    # Return health status
    return jsonify({
        "status": "healthy",
        "article_count": article_count,
        "timestamp": time.time()
    })

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
            "GET /json": "Get the entire dataset as a static JSON file",
            "GET /logs": "View application logs",
            "GET /debug": "Get debug information about the environment"
        }
    }
    return jsonify(endpoints)

@app.route('/articles')
def get_articles():
    """Get all articles with optional pagination and filtering"""
    # Parse query parameters
    limit = request.args.get('limit', default=None, type=int)  # No default limit
    offset = request.args.get('offset', default=0, type=int)
    source = request.args.get('source', default=None, type=str)
    
    logger.info(f"API request: /articles with limit={limit}, offset={offset}, source={source}")
    
    # First check if we have a JSON file with articles
    json_file_path = 'gaming_news.json'
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                json_articles = json_data.get('articles', [])
                logger.info(f"Found {len(json_articles)} articles in JSON file")
                
                # Filter by source if needed
                if source:
                    json_articles = [a for a in json_articles if a.get('source_name', '').lower() == source.lower()]
                
                # Apply pagination - no default limit
                total_count = len(json_articles)
                paginated_articles = json_articles[offset:offset+limit] if limit is not None else json_articles[offset:]
                
                # Format articles
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
                    ]) for article in paginated_articles
                ]
                
                logger.info(f"Returning {len(formatted_articles)} articles from JSON file")
                return jsonify({
                    "total": total_count,
                    "offset": offset,
                    "limit": limit,
                    "articles": formatted_articles
                })
        except Exception as e:
            logger.error(f"Error reading from JSON file: {str(e)}")
            logger.error(traceback.format_exc())
            # Continue to database as fallback
    
    # Get articles from database as fallback
    logger.info("Falling back to database query")
    articles = db.get_all_articles(limit=limit, offset=offset, source=source)
    total_count = db.get_article_count(source=source)
    logger.info(f"Found {len(articles)} articles in database (total: {total_count})")
    
    # If no articles found, use fallback data as last resort
    if not articles:
        logger.warning("No articles in database, using fallback data as last resort")
        articles = get_fallback_articles()
        total_count = len(articles)
        logger.info(f"Using {total_count} fallback articles")
        
        # Try to add fallback articles to database in a background thread to avoid blocking
        def add_fallback_articles_background():
            try:
                db.add_articles(articles)
                db.export_to_json()
                logger.info("Successfully added fallback articles to database and exported to JSON")
            except Exception as e:
                logger.error(f"Failed to add fallback articles to database: {str(e)}")
                logger.error(traceback.format_exc())
        
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
    logger.info(f"Returning {len(formatted_articles)} articles from database")
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

@app.route('/logs')
def view_logs():
    """View application logs"""
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
            # Get the last 500 lines (most recent logs)
            logs = logs[-500:]
            return jsonify({
                "status": "success",
                "log_count": len(logs),
                "logs": logs
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Log file {log_file} not found"
            }), 404
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error reading logs: {str(e)}"
        }), 500

@app.route('/debug')
def debug_info():
    """Get debug information about the environment"""
    try:
        # Get information about the environment
        env_info = {
            "environment": "Railway" if 'RAILWAY_ENVIRONMENT' in os.environ else "Local",
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "files_in_root": os.listdir('.'),
            "content_files": os.listdir('content') if os.path.exists('content') else [],
            "image_files": os.listdir('images') if os.path.exists('images') else [],
            "database_exists": os.path.exists('news.db'),
            "json_exists": os.path.exists('gaming_news.json'),
            "json_size": os.path.getsize('gaming_news.json') if os.path.exists('gaming_news.json') else 0,
            "article_count_in_db": db.get_article_count(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # If JSON file exists, get article count from it
        if os.path.exists('gaming_news.json'):
            try:
                with open('gaming_news.json', 'r') as f:
                    json_data = json.load(f)
                    env_info["article_count_in_json"] = json_data.get('article_count', 0)
            except Exception as e:
                env_info["json_error"] = str(e)
        
        return jsonify({
            "status": "success",
            "debug_info": env_info
        })
    except Exception as e:
        logger.error(f"Error getting debug info: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error getting debug info: {str(e)}"
        }), 500

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
