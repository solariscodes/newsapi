# Gaming News API

A gaming news scraper and API that collects articles from multiple gaming news sources, stores them in SQLite, and serves them via a REST API. This application uses a hybrid SQLite + JSON approach for efficient storage and serving of data.

## Features

- Scrapes articles from multiple gaming news websites
- Stores data in SQLite database with deduplication
- Exports to JSON for compatibility
- RESTful API for accessing articles
- Automatic scheduled scraping
- Ready for Railway deployment

## API Endpoints

- `GET /` - API documentation
- `GET /articles` - Get all articles with pagination
  - Query params: `limit`, `offset`, `source`
- `GET /articles/<article_id>` - Get a specific article by ID
- `GET /articles/sources` - Get list of available news sources
- `GET /articles/search?q=<query>` - Search articles by keyword
- `GET /json` - Get the entire dataset as a static JSON file

## Local Development

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running Locally

1. Run the scraper to collect articles:
   ```
   python scraper.py --db
   ```

2. Start the API server:
   ```
   python app.py
   ```

3. Access the API at `http://localhost:5000`

## Deployment to Railway

This project is configured for easy deployment to Railway.

### Steps to Deploy

1. Connect your Git repository to Railway
2. Create a new project
3. Railway will automatically detect the Python application
4. Deploy!

The application uses Nixpacks for building and Gunicorn for serving the application, which is all configured in the `railway.json` file.

### File Storage on Railway

Railway provides ephemeral storage, which means files (including the SQLite database and images) will persist only until the next deployment. For production use, consider implementing cloud storage for images and using a managed database service.

## Architecture

This application uses a hybrid approach:

1. **SQLite Database**: For storage and deduplication
2. **JSON Export**: For compatibility and direct consumption
3. **Flask API**: For serving the data

This design provides a good balance of:
- Low operational cost
- Simple maintenance
- Reliable deduplication
- Easy deployment

## Security Considerations

- The application serves read-only data
- No user authentication required
- All API endpoints are public
- Rate limiting is implemented to prevent abuse

## Customization

- Add new scrapers in the `scrapers/` directory
- Adjust scraping frequency in `app.py`
- Modify the API endpoints in `app.py`
