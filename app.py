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
        # Run the scraper with database integration
        result = subprocess.run(
            ["python", "scraper.py", "--db"],
            capture_output=True, 
            text=True, 
            check=True
        )
        logger.info(f"Scraper completed: {result.stdout}")
        
        # Export the latest data to JSON for API consumers who prefer it
        article_count = db.export_to_json()
        logger.info(f"Exported {article_count} articles to JSON")
    except subprocess.CalledProcessError as e:
        logger.error(f"Scraper failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")

# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_scraper, 'interval', hours=6)  # Run every 6 hours

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
    limit = request.args.get('limit', default=None, type=int)  # Default to no limit
    offset = request.args.get('offset', default=0, type=int)
    source = request.args.get('source', default=None, type=str)
    
    # Get articles from database
    articles = db.get_all_articles(limit=limit, offset=offset, source=source)
    total_count = db.get_article_count(source=source)
    
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
    
    # Return response with the formatted articles
    return jsonify({
        "total": total_count,
        "offset": offset,
        "limit": limit if limit else total_count,
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
