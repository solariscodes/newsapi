#!/usr/bin/env python3
import os
import json
import sqlite3
import hashlib
import threading
from datetime import datetime
from collections import OrderedDict

class NewsDatabase:
    def __init__(self, db_path="news.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.thread_local = threading.local()
        self.create_tables()

    def connect(self):
        """Create a connection to the SQLite database that's thread-safe"""
        if not hasattr(self.thread_local, 'conn'):
            self.thread_local.conn = sqlite3.connect(self.db_path)
            self.thread_local.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        return self.thread_local.conn

    def close(self):
        """Close the database connection"""
        if hasattr(self.thread_local, 'conn'):
            self.thread_local.conn.close()
            delattr(self.thread_local, 'conn')

    def create_tables(self):
        """Create the necessary tables if they don't exist"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            published_date TEXT,
            image_url TEXT,
            local_image_path TEXT,
            local_content_path TEXT,
            scrape_timestamp TEXT NOT NULL,
            UNIQUE(source_url)
        )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrape_timestamp ON articles(scrape_timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_name ON articles(source_name)')
        
        # Create export_history table to track JSON exports
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS export_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            filename TEXT NOT NULL,
            article_count INTEGER NOT NULL
        )
        ''')
        
        conn.commit()

    def generate_article_id(self, article):
        """Generate a unique ID for an article based on title and URL"""
        # Create a string combining unique aspects of the article
        unique_string = f"{article.get('title', '')}{article.get('source_url', '')}"
        # Generate a hash
        return hashlib.md5(unique_string.encode()).hexdigest()

    def article_exists(self, article):
        """Check if an article already exists in the database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Check by URL first (most reliable)
        cursor.execute("SELECT id FROM articles WHERE source_url = ?", 
                      (article.get('source_url', ''),))
        if cursor.fetchone():
            return True
            
        # If no URL match, check by title and source
        if article.get('title') and article.get('source_name'):
            cursor.execute("SELECT id FROM articles WHERE title = ? AND source_name = ?", 
                          (article.get('title', ''), article.get('source_name', '')))
            if cursor.fetchone():
                return True
                
        return False

    def add_article(self, article):
        """Add a new article to the database if it doesn't already exist"""
        if self.article_exists(article):
            return False  # Article already exists
            
        conn = self.connect()
        cursor = conn.cursor()
        
        # Generate unique ID for the article
        article_id = self.generate_article_id(article)
        
        # Current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure content is in the article or read from content file
        content = article.get('content', '')
        if not content.strip() and 'content_file_path' in article:
            content_path = article.get('content_file_path')
            try:
                if os.path.exists(content_path):
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = f.read()
            except Exception as e:
                print(f"Error reading content from {content_path}: {e}")
        
        # Insert the article
        cursor.execute('''
        INSERT INTO articles (
            id, title, description, content, source_name, source_url, 
            published_date, image_url, local_image_path, local_content_path, scrape_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_id,
            article.get('title', ''),
            article.get('description', ''),
            content,
            article.get('source_name', ''),
            article.get('source_url', ''),
            article.get('published_date', ''),
            article.get('image_url', ''),
            article.get('local_image_path', ''),
            article.get('content_file_path', ''),
            now
        ))
        
        conn.commit()
        return True

    def add_articles(self, articles):
        """Add multiple articles and return count of new additions"""
        added_count = 0
        for article in articles:
            if self.add_article(article):
                added_count += 1
        return added_count

    def get_all_articles(self, limit=None, offset=0, source=None):
        """Get all articles with optional filtering"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Select only the necessary fields to improve performance
        query = """SELECT id, title, content, source_name, source_url, 
                 image_url, local_image_path, local_content_path, scrape_timestamp 
                 FROM articles"""
        params = []
        
        # Add source filter if provided
        if source:
            query += " WHERE source_name = ?"
            params.append(source)
            
        # Add ordering
        query += " ORDER BY scrape_timestamp DESC"
        
        # Add limit and offset
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        elif offset > 0:
            # If only offset is provided (no limit)
            query += " LIMIT -1 OFFSET ?"
            params.append(offset)
            
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_article_by_id(self, article_id):
        """Get a specific article by ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_article_sources(self):
        """Get a list of all unique article sources"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT source_name FROM articles")
        return [row[0] for row in cursor.fetchall()]

    def get_article_count(self, source=None):
        """Get the total number of articles in the database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM articles"
        params = []
        
        if source:
            query += " WHERE source_name = ?"
            params.append(source)
            
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def export_to_json(self, output_file='gaming_news.json'):
        """Export all articles to a JSON file"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get all articles
        cursor.execute("SELECT * FROM articles ORDER BY scrape_timestamp DESC")
        articles = [dict(row) for row in cursor.fetchall()]
        
        # Get content from content files if content field is empty
        formatted_articles = []
        for article in articles:
            # Make sure content is included
            if not article.get('content') or article['content'].strip() == '':
                # Try to read from content file if we stored a path
                content_path = article.get('local_content_path')
                if content_path and os.path.exists(content_path):
                    try:
                        with open(content_path, 'r', encoding='utf-8') as f:
                            article['content'] = f.read()
                    except Exception as e:
                        print(f"Error reading content file {content_path}: {e}")
                
                # If still empty, try to create a default message
                if not article.get('content') or article['content'].strip() == '':
                    article['content'] = f"Visit the source for more information: {article.get('source_url', 'Unknown source')}"
            
            # Create a new dictionary with ordered keys and only necessary fields
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
        
        # Create JSON structure
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "scrape_timestamp": timestamp,
            "article_count": len(formatted_articles),
            "articles": formatted_articles
        }
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        # Record this export
        cursor.execute(
            "INSERT INTO export_history (timestamp, filename, article_count) VALUES (?, ?, ?)",
            (timestamp, output_file, len(formatted_articles))
        )
        conn.commit()
        
        return len(formatted_articles)

    def search_articles(self, query, limit=10, offset=0):
        """Search for articles by keyword"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Search in title and content
        search_term = f"%{query}%"
        cursor.execute('''
        SELECT * FROM articles 
        WHERE title LIKE ? OR content LIKE ? 
        ORDER BY scrape_timestamp DESC
        LIMIT ? OFFSET ?
        ''', (search_term, search_term, limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
