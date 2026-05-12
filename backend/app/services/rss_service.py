import feedparser
import httpx
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from app.config import settings
from app.database import get_db
from app.models import ArticleInDB
from pymongo.errors import DuplicateKeyError
import asyncio

logger = logging.getLogger(__name__)

def extract_image_url(entry):
    # 1. Check media_content
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0].get('url')
    
    # 2. Check links
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')
                
    # 3. Parse description for img tag
    desc = entry.get('summary', '') or entry.get('description', '')
    if desc:
        soup = BeautifulSoup(desc, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img.get('src')
    
    return None

def clean_summary(summary_html: str) -> str:
    if not summary_html:
        return ""
    soup = BeautifulSoup(summary_html, 'html.parser')
    # Remove img tags and other formatting to get clean text
    return soup.get_text(strip=True)

async def fetch_and_parse_feed(feed_config: dict):
    url = feed_config['url']
    name = feed_config['name']
    category = feed_config['category']
    
    logger.info(f"Fetching feed: {name} from {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        feed = feedparser.parse(response.content)
        
        db = get_db()
        if db is None:
            logger.error("Database connection not available")
            return
            
        new_count = 0
        
        for entry in feed.entries:
            link = entry.get('link')
            if not link:
                continue
                
            # Handle dates safely
            pub_date_raw = entry.get('published') or entry.get('updated')
            if pub_date_raw:
                try:
                    published_at = date_parser.parse(pub_date_raw)
                except:
                    published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()
                
            summary_raw = entry.get('summary', '') or entry.get('description', '')
            clean_txt = clean_summary(summary_raw)
            img_url = extract_image_url(entry)
            
            article = ArticleInDB(
                title=entry.get('title', 'No Title'),
                link=link,
                summary=clean_txt,
                content_snippet=clean_txt[:200],
                published_at=published_at,
                source_name=name,
                category=category,
                image_url=img_url
            )
            
            try:
                await db.articles.insert_one(article.model_dump(by_alias=True, exclude={'id'}))
                new_count += 1
            except DuplicateKeyError:
                # Already exists, skip
                pass
                
        logger.info(f"Finished {name}: Inserted {new_count} new articles")
        
    except Exception as e:
        logger.error(f"Error processing feed {name}: {str(e)}", exc_info=True)

async def run_all_aggregations():
    logger.info("Starting aggregation cycle...")
    db = get_db()
    if db is None:
        logger.error("DB not initialized for aggregation.")
        return
        
    # Query active sources from DB
    cursor = db.sources.find({"is_active": True})
    sources = await cursor.to_list(length=1000)
    
    if not sources:
        logger.info("No active sources found in DB.")
        return
        
    tasks = [fetch_and_parse_feed(feed) for feed in sources]
    await asyncio.gather(*tasks)
    logger.info("Completed aggregation cycle.")
