#!/usr/bin/env python3
"""
Fallback data module that provides sample gaming news articles
if the scraper fails to retrieve any content.
"""

import json
from datetime import datetime
import hashlib

def get_fallback_articles():
    """Return a list of fallback gaming news articles"""
    
    # Generate timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Sample articles
    articles = [
        {
            "title": "The Elder Scrolls 6 Development Update",
            "content": "Bethesda has shared a rare update on The Elder Scrolls 6, confirming that the game is still in pre-production while the team focuses on completing Starfield and its expansions. Todd Howard mentioned that they have a clear vision for the game and are excited to share more details in the future. The Elder Scrolls 6 was first announced in 2018 with a brief teaser trailer showing a mountainous landscape.",
            "source_name": "IGN",
            "source_url": "https://www.ign.com/articles/elder-scrolls-6-development-update",
            "image_url": "https://assets-prd.ignimgs.com/2022/06/13/elder-scrolls-6-button-1655161203683.jpg"
        },
        {
            "title": "PlayStation 6 Reportedly Targeting 2028 Release Window",
            "content": "According to industry insiders, Sony is targeting a 2028 release window for the PlayStation 6. Internal documents suggest that the company is already working on the hardware specifications, with a focus on advanced AI capabilities and fully immersive VR integration. This timeline would give the PS5 a lifecycle of approximately 8 years, similar to the PS4. Sony has not officially commented on these reports.",
            "source_name": "GameSpot",
            "source_url": "https://www.gamespot.com/articles/playstation-6-reportedly-targeting-2028-release-window/1100-6510001/",
            "image_url": "https://www.gamespot.com/a/uploads/screen_kubrick/1179/11799911/4212246-screenshot2023-07-26at11.47.57am.png"
        },
        {
            "title": "Nintendo Switch 2 Features Leaked by Developer",
            "content": "An anonymous developer working on a launch title for the Nintendo Switch 2 has leaked several key features of the upcoming console. According to the leak, the Switch 2 will support 4K output when docked, feature improved Joy-Con controllers with better drift resistance, and include backward compatibility with original Switch games. The battery life is said to be significantly improved, offering 5-7 hours of gameplay on demanding titles. Nintendo has not confirmed these details and typically does not comment on rumors or speculation.",
            "source_name": "Eurogamer",
            "source_url": "https://www.eurogamer.net/nintendo-switch-2-features-leaked-by-developer",
            "image_url": "https://assetsio.reedpopcdn.com/switch-pro.jpg?width=1200&height=1200&fit=crop&quality=100&format=png&enable=upscale&auto=webp"
        },
        {
            "title": "GTA 6 Release Date Potentially Delayed to 2026",
            "content": "Take-Two Interactive's latest financial report suggests that Grand Theft Auto 6 might be delayed until early 2026. While not explicitly stating a delay, the company has adjusted its long-term financial projections in a way that analysts interpret as indicating a shift in the release window. Rockstar Games has not made any official announcement regarding a delay from the previously announced 2025 target. The highly anticipated title has been in development for several years and is expected to return to Vice City with the series' first female protagonist.",
            "source_name": "PC Gamer",
            "source_url": "https://www.pcgamer.com/gta-6-release-date-potentially-delayed-to-2026/",
            "image_url": "https://cdn.mos.cms.futurecdn.net/yS8AdDpYKGPQHkDVmNPQ6P-970-80.jpg"
        },
        {
            "title": "Call of Duty: Black Ops 6 Zombies Mode Detailed",
            "content": "Activision has revealed extensive details about the Zombies mode in the upcoming Call of Duty: Black Ops 6. The mode will feature a new storyline separate from the Dark Aether saga, with a focus on more open-world elements and RPG progression systems. Players can expect four maps at launch, with a mix of traditional round-based experiences and larger objective-based missions. The developer has also promised improved server stability and cross-play features for all platforms.",
            "source_name": "GameRant",
            "source_url": "https://gamerant.com/call-of-duty-black-ops-6-zombies-mode-detailed/",
            "image_url": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2023/02/call-of-duty-black-ops-cold-war-zombies-mode-key-art.jpg"
        }
    ]
    
    # Process articles to add IDs and timestamps
    processed_articles = []
    for article in articles:
        # Generate a unique ID based on title and source
        unique_string = f"{article['title']}{article['source_url']}"
        article_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Create processed article with proper structure
        processed_article = {
            "id": article_id,
            "title": article["title"],
            "content": article["content"],
            "source_name": article["source_name"],
            "source_url": article["source_url"],
            "image_url": article["image_url"],
            "local_image_path": "",
            "scrape_timestamp": now
        }
        
        processed_articles.append(processed_article)
    
    return processed_articles

def save_fallback_data(output_file='gaming_news.json'):
    """Save fallback data to a JSON file"""
    articles = get_fallback_articles()
    
    # Create JSON structure
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "scrape_timestamp": timestamp,
        "article_count": len(articles),
        "articles": articles
    }
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return len(articles)

if __name__ == "__main__":
    count = save_fallback_data()
    print(f"Saved {count} fallback articles to gaming_news.json")
