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
from app.services.notifier_service import broadcast_new_article
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
    candidates = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        feed = feedparser.parse(response.content)
        
        db = get_db()
        if db is None:
            return []
            
        # Pre-cache existing links in this batch to avoid insertion checks later
        links_in_feed = [entry.get('link') for entry in feed.entries if entry.get('link')]
        existing_links_cursor = db.articles.find({"link": {"$in": links_in_feed}}, {"link": 1})
        existing_links = {doc["link"] async for doc in existing_links_cursor}
        
        for entry in feed.entries:
            link = entry.get('link')
            if not link or link in existing_links:
                continue
                
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
            
            candidates.append({
                "title": entry.get('title', 'No Title'),
                "link": link,
                "summary": clean_txt,
                "content_snippet": clean_txt[:200],
                "published_at": published_at,
                "source_name": name,
                "category": category,
                "image_url": img_url
            })
                
        logger.info(f"Parsed {name}: Found {len(candidates)} new dynamic entries.")
        return candidates
        
    except Exception as e:
        logger.error(f"Error fetching feed {name}: {str(e)}")
        return []

async def run_all_aggregations():
    logger.info("Starting aggregation cycle...")
    db = get_db()
    if db is None:
        return
        
    cursor = db.sources.find({"is_active": True})
    sources = await cursor.to_list(length=1000)
    if not sources:
        return
        
    # 1. Gather dynamic results from parallel fetching tasks
    tasks = [fetch_and_parse_feed(feed) for feed in sources]
    results = await asyncio.gather(*tasks)
    
    # Flatten list of candidate dictionaries
    all_candidates = []
    for res in results:
        all_candidates.extend(res)
        
    if not all_candidates:
        logger.info("Zero incoming items discovered across all streams.")
        return
        
    # 2. OPTIONAL: Execute AI-Powered Batch Semantic Deduplication
    from app.services.ai_service import analyze_batch_duplicates
    from pymongo import DESCENDING
    
    # Grab the recent history of articles (last ~50)
    recent_cursor = db.articles.find({}, {"title": 1}).sort("published_at", DESCENDING).limit(50)
    recent_in_db = [doc async for doc in recent_cursor]
    
    # Dispatch to AI to calculate semantic collision map
    duplicate_map = await analyze_batch_duplicates(all_candidates, recent_in_db)
    
    # 3. Process Final Persistence Loop
    new_count = 0
    for raw_art in all_candidates:
        link = raw_art["link"]
        
        # Instantiate final runtime model including AI resolution markers
        article = ArticleInDB(
            **raw_art,
            is_duplicate=link in duplicate_map,
            duplicate_of_title=duplicate_map.get(link)
        )
        
        try:
            await db.articles.insert_one(article.model_dump(by_alias=True, exclude={'id'}))
            new_count += 1
        except Exception:
            # Final fail-safe check against link dups
            pass
            
    logger.info(f"Ingestion phase finished. Inserted {new_count} unique documents.")

    # 4. FINAL FLUSH: Execute broadcast dispatch on clean queues
    from app.services.notifier_service import process_pending_notifications
    await process_pending_notifications(limit=30)
    
    logger.info("Full aggregation lifecycle completed.")
