import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "social_trending")
    RSS_POLL_INTERVAL_MINUTES: int = 15
    
    RSS_FEEDS: list = [
        # Sample Vietnamese news RSS feeds
        {"name": "VnExpress - Tin mới nhất", "url": "https://vnexpress.net/rss/tin-moi-nhat.rss", "category": "General"},
        {"name": "Tuổi Trẻ - Tin mới nhất", "url": "https://tuoitre.vn/rss/tin-moi-nhat.rss", "category": "General"},
        {"name": "Thanh Niên - Tin mới nhất", "url": "https://thanhnien.vn/rss/home.rss", "category": "General"},
        {"name": "NYT - HomePage", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "category": "Global"},
        {"name": "NYT - World", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "category": "Global"},
        {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "Global"},
        {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best", "category": "Global"},
        {"name": "BBC News - World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "Global"},
        {"name": "Washington Post", "url": "https://feeds.washingtonpost.com/rss/world", "category": "Global"},
        {"name": "WSJ Opinion", "url": "https://feeds.a.dj.com/rss/RSSOpinion.xml", "category": "Finance"},
        {"name": "FT World", "url": "https://www.ft.com/world?format=rss", "category": "Finance"},
        {"name": "The Economist", "url": "https://www.economist.com/central-and-eastern-europe/rss.xml", "category": "Finance"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
        {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
        {"name": "SCMP China", "url": "https://www.scmp.com/rss/2/feed", "category": "Asia"},
        {"name": "SCMP Asia", "url": "https://www.scmp.com/rss/4/feed", "category": "Asia"},
        {"name": "The Japan Times", "url": "https://www.japantimes.co.jp/feed/", "category": "Asia"},
    ]

    class Config:
        env_file = ".env"

settings = Settings()
