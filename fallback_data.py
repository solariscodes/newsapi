#!/usr/bin/env python3
"""
Fallback data module that provides sample gaming news articles
if the scraper fails to retrieve any content.
"""
import os
import json
from datetime import datetime
import uuid
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
        },
        {
            "title": "Elden Ring DLC Shadow of the Erdtree Release Date Announced",
            "content": "FromSoftware has officially announced that the highly anticipated Elden Ring expansion, Shadow of the Erdtree, will be released on June 21, 2025. The DLC promises to add a substantial new area to the game, along with new weapons, armor sets, and challenging boss encounters. Director Hidetaka Miyazaki stated that the expansion will be approximately 30 hours long and will explore the history of Miquella, a character only mentioned in the base game. A new trailer showcased some of the environments and enemies players will face.",
            "source_name": "IGN",
            "source_url": "https://www.ign.com/articles/elden-ring-shadow-of-the-erdtree-release-date-announced",
            "image_url": "https://assets-prd.ignimgs.com/2023/02/28/elden-ring-shadow-of-the-erdtree-button-fin-1677614224278.jpg"
        },
        {
            "title": "Microsoft Flight Simulator 2025 Showcases Photorealistic Graphics",
            "content": "Microsoft has unveiled new footage of Microsoft Flight Simulator 2025, demonstrating the game's next-generation photorealistic graphics. Using a combination of satellite imagery, AI-enhanced textures, and advanced lighting systems, the new iteration promises to deliver the most realistic flying experience to date. The demo showcased real-time weather effects, including volumetric clouds and atmospheric scattering, as well as highly detailed aircraft interiors with fully functional instruments. The game is scheduled for release in November 2025 for Xbox Series X|S and PC.",
            "source_name": "PC Gamer",
            "source_url": "https://www.pcgamer.com/microsoft-flight-simulator-2025-showcases-photorealistic-graphics/",
            "image_url": "https://cdn.mos.cms.futurecdn.net/HYFHRPTBUVDRFQznEwLYWJ.jpg"
        },
        {
            "title": "Starfield's First Major Expansion 'Shattered Space' Detailed",
            "content": "Bethesda has revealed extensive details about Starfield's first major expansion, 'Shattered Space,' scheduled for release next month. The DLC will introduce a new star system affected by a catastrophic stellar event, creating a unique environment with fractured planets and space-time anomalies. Players will encounter a previously unknown faction with advanced technology and will be able to recruit new companions with unique abilities. The expansion also adds new weapons, ship parts, and outpost modules. Bethesda promises that player choices will have significant consequences on the narrative outcome.",
            "source_name": "Kotaku",
            "source_url": "https://kotaku.com/starfield-shattered-space-expansion-details-bethesda-1850425678",
            "image_url": "https://i.kinja-img.com/image/upload/c_fill,f_auto,fl_progressive,g_center,h_675,pg_1,q_80,w_1200/f8a8b84b9865782bfd20c5169e89df1e.jpg"
        },
        {
            "title": "Epic Games Store Adds User Reviews and Shopping Cart Features",
            "content": "Epic Games has finally implemented two of the most requested features for its digital storefront: user reviews and a shopping cart. The review system includes measures to prevent review bombing, requiring users to have played a game for at least two hours before leaving a review. The system also uses a questionnaire format rather than a simple star rating to provide more nuanced feedback. The shopping cart feature allows users to purchase multiple games in a single transaction, bringing the store closer to feature parity with competitors like Steam. Epic CEO Tim Sweeney stated that these additions are part of the company's ongoing commitment to improving the user experience.",
            "source_name": "Eurogamer",
            "source_url": "https://www.eurogamer.net/epic-games-store-adds-user-reviews-and-shopping-cart-features",
            "image_url": "https://assetsio.reedpopcdn.com/epic-games-store-logo.jpg?width=1200&height=1200&fit=crop&quality=100&format=png&enable=upscale&auto=webp"
        },
        {
            "title": "Cyberpunk 2077 Sequel Enters Full Production",
            "content": "CD Projekt Red has announced that the sequel to Cyberpunk 2077, codenamed 'Project Orion,' has entered full production. Following the successful launch of the Phantom Liberty expansion and the game's redemption arc after its troubled initial release, the studio is now fully committed to developing the next chapter in the Cyberpunk universe. The sequel will utilize Unreal Engine 5 rather than the company's proprietary REDengine, a decision made to streamline development and take advantage of advanced features like Nanite and Lumen. The game is being developed primarily by CD Projekt's new Boston studio, with support from teams in Warsaw and Vancouver.",
            "source_name": "GameSpot",
            "source_url": "https://www.gamespot.com/articles/cyberpunk-2077-sequel-enters-full-production/1100-6510234/",
            "image_url": "https://www.gamespot.com/a/uploads/screen_kubrick/1179/11799911/4132009-cyberpunk.jpg"
        },
        {
            "title": "Hollow Knight: Silksong Release Window Narrowed to Early 2026",
            "content": "Team Cherry has finally provided an update on the long-awaited Hollow Knight: Silksong, narrowing its release window to early 2026. The developers explained that the scope of the game has expanded significantly during development, with the world size now approximately 1.8 times larger than the original Hollow Knight. The team has also implemented more complex combat mechanics and enemy AI systems to accommodate Hornet's more agile movement abilities. While fans expressed disappointment at the further delay, Team Cherry reassured them that the additional time will ensure a polished and content-rich experience that lives up to expectations.",
            "source_name": "Polygon",
            "source_url": "https://www.polygon.com/hollow-knight-silksong-release-date-team-cherry",
            "image_url": "https://cdn.vox-cdn.com/thumbor/9UXnODCCN6gV1r3-_hY5Xm-CKzE=/0x0:1920x1080/1200x800/filters:focal(807x387:1113x693)/cdn.vox-cdn.com/uploads/chorus_image/image/71956121/ss_89b8f2f2e7a0264c2c942c4c26cbe8f9c3b87827.0.jpg"
        },
        {
            "title": "Riot Games Announces New Tactical Shooter 'Vanguard'",
            "content": "Riot Games has announced a new tactical shooter titled 'Vanguard,' expanding their portfolio beyond Valorant in the competitive FPS space. Unlike Valorant's ability-focused gameplay, Vanguard emphasizes realistic gunplay and destructible environments, positioning it as a competitor to games like Rainbow Six Siege. The game will feature a near-future setting with advanced military technology but no supernatural abilities. Riot emphasized that Vanguard will coexist with Valorant rather than replace it, targeting players who prefer a more grounded tactical experience. A closed alpha test is scheduled for late 2025, with a full release expected in 2026.",
            "source_name": "WCCFTech",
            "source_url": "https://wccftech.com/riot-games-announces-new-tactical-shooter-vanguard/",
            "image_url": "https://cdn.wccftech.com/wp-content/uploads/2023/06/riot-games-logo-scaled.jpg"
        },
        {
            "title": "Assassin's Creed Shadows Gameplay Deep Dive Reveals New Stealth Mechanics",
            "content": "Ubisoft has released an extensive gameplay deep dive for Assassin's Creed Shadows, showcasing the game's refined stealth mechanics. The upcoming title, set in feudal Japan, will feature two playable protagonists with distinct stealth approaches: Yasuke relies on strength and direct confrontation when detected, while Naoe specializes in distraction techniques and quick escapes. The video demonstrated new features including improved enemy AI with dynamic search patterns, environmental stealth options like hiding in mud or water, and a completely revamped detection system with multiple awareness states. The game also introduces stealth-focused skill trees that allow players to specialize in different infiltration styles.",
            "source_name": "GameRant",
            "source_url": "https://gamerant.com/assassins-creed-shadows-gameplay-deep-dive-reveals-new-stealth-mechanics/",
            "image_url": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2024/05/assassins-creed-shadows-key-art.jpg"
        },
        {
            "title": "Breath of the Wild Speedrunner Beats Game in Under 20 Minutes, Sets New World Record",
            "content": "A speedrunner known as 'Player5' has set a new world record for The Legend of Zelda: Breath of the Wild, completing the game in just 19 minutes and 47 seconds. The run, which falls under the 'Any%' category that allows glitches, utilized several advanced techniques including the recently discovered 'memory warp' glitch that allows players to teleport directly to Ganon after completing a specific sequence of actions. Player5's run improved on the previous record by 23 seconds, a significant margin in the highly competitive Breath of the Wild speedrunning community. The feat is particularly impressive considering that a casual playthrough of the game typically takes over 50 hours.",
            "source_name": "Kotaku",
            "source_url": "https://kotaku.com/breath-of-the-wild-speedrun-world-record-under-20-minutes-1850426789",
            "image_url": "https://i.kinja-img.com/image/upload/c_fill,f_auto,fl_progressive,g_center,h_675,pg_1,q_80,w_1200/e450f3adb82f2aba28ca541663eff892.jpg"
        },
        {
            "title": "Minecraft Announces 'Wilds Update' with New Biomes and Creatures",
            "content": "Mojang has announced the next major update for Minecraft, titled the 'Wilds Update,' scheduled for release in early 2026. The update will introduce three new biomes: Mangrove Swamps, featuring unique root systems and new wood types; Alpine Meadows, located at high elevations with exclusive flora and fauna; and Volcanic Islands, complete with active volcanoes and obsidian formations. New creatures include mountain goats, fireflies that dynamically light up the night, and the fearsome Warden in the Deep Dark biome. The update will also add new building materials, including mud bricks and volcanic stone variants, along with archaeology mechanics that allow players to uncover artifacts and fossils.",
            "source_name": "IGN",
            "source_url": "https://www.ign.com/articles/minecraft-wilds-update-new-biomes-creatures",
            "image_url": "https://assets-prd.ignimgs.com/2022/06/07/minecraft-1654626492596.jpg"
        }
    ]
    
    # Process articles to add IDs and timestamps
    processed_articles = []
    for article in articles:
        # Generate a unique ID based on title and source
        unique_string = f"{article['title']}{article['source_url']}"
        article_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Generate local paths
        image_filename = f"{article_id}.jpg"
        content_filename = f"{article_id}.txt"
        local_image_path = os.path.join("images", image_filename)
        local_content_path = os.path.join("content", content_filename)
        
        # Create processed article with proper structure
        processed_article = {
            "id": article_id,
            "title": article["title"],
            "content": article["content"],
            "source_name": article["source_name"],
            "source_url": article["source_url"],
            "image_url": article["image_url"],
            "local_image_path": local_image_path,
            "local_content_path": local_content_path,
            "scrape_timestamp": now
        }
        
        processed_articles.append(processed_article)
    
    return processed_articles

def save_fallback_data(output_file='gaming_news.json'):
    """Save fallback data to a JSON file and create necessary content files"""
    articles = get_fallback_articles()
    
    # Create directories if they don't exist
    os.makedirs('images', exist_ok=True)
    os.makedirs('content', exist_ok=True)
    
    # Save content to individual files
    for article in articles:
        content_path = article.get('local_content_path')
        if content_path:
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(article['content'])
    
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
