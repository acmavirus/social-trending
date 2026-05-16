import json
import re
import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from app.database import get_db
from app.models import ArticleInDB
from app.services.notifier_service import broadcast_new_article

logger = logging.getLogger(__name__)

def find_nested_key(d, key_to_find):
    if isinstance(d, dict):
        if key_to_find in d:
            return d[key_to_find]
        for v in d.values():
            res = find_nested_key(v, key_to_find)
            if res: return res
    elif isinstance(d, list):
        for item in d:
            res = find_nested_key(item, key_to_find)
            if res: return res
    return None

async def scrape_threads_profile(username: str = "trending"):
    url = f"https://www.threads.net/@{username}"
    headers = {
        "authority": "www.threads.net",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "dnt": "1",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    candidates = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Threads crawler blocked with code {response.status_code}")
                return []
            
            html_content = response.text
            
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all("script", attrs={"data-sjs": True})
        
        found_data = None
        for script in scripts:
            if "BarcelonaProfileThreadsTabDirectQuery" in script.text:
                try:
                    # Preprocess potential double slashes or issues if necessary, usually direct json.loads works
                    parsed = json.loads(script.text)
                    found_data = find_nested_key(parsed, "mediaData")
                    if found_data:
                        break
                except Exception:
                            continue
        
        if not found_data:
            logger.warning(f"Could not locate mediaData in Threads profile JSON for @{username}")
            return []
            
        edges = found_data.get("edges", [])
        for edge in edges:
            try:
                node = edge.get("node", {})
                thread_items = node.get("thread_items", [])
                if not thread_items:
                    continue
                
                post = thread_items[0].get("post", {})
                if not post:
                    continue
                    
                post_code = post.get("code")
                if not post_code:
                    continue
                    
                post_url = f"https://www.threads.net/@{username}/post/{post_code}"
                
                caption_data = post.get("caption") or {}
                text_content = caption_data.get("text", "")
                
                # Truncate title for cleaner display
                clean_title = text_content.split("\n")[0][:100] or "Threads Update"
                
                taken_at = post.get("taken_at")
                published_at = datetime.utcfromtimestamp(taken_at) if taken_at else datetime.utcnow()
                
                image_url = None
                img_versions = post.get("image_versions2") or {}
                candidates_imgs = img_versions.get("candidates", [])
                if candidates_imgs:
                    image_url = candidates_imgs[0].get("url")

                candidates.append({
                    "title": clean_title,
                    "link": post_url,
                    "summary": text_content,
                    "content_snippet": text_content[:200],
                    "published_at": published_at,
                    "source_name": f"Threads @{username}",
                    "category": "Social Trending",
                    "image_url": image_url
                })
            except Exception as sub_e:
                logger.warning(f"Skipping single threads post due to parse error: {sub_e}")
                
        return candidates
        
    except Exception as e:
        logger.error(f"Threads scraping general failure: {str(e)}")
        return []

async def run_threads_aggregation():
    logger.info("Running Threads aggregation pipeline...")
    db = get_db()
    if db is None: return
    
    # Fetch active Threads sources from DB
    cursor = db.social_sources.find({"platform": "Threads", "is_active": True})
    sources = await cursor.to_list(length=100)
    
    if not sources:
        # Fallback to default if none configured
        logger.info("No Threads sources configured. Following default @trending")
        sources = [{"username": "trending"}]
        
    for source_config in sources:
        username = source_config["username"]
        logger.info(f"Processing Threads account: @{username}")
        
        # Fetch new candidates
        candidates = await scrape_threads_profile(username)
        if not candidates:
            logger.info(f"No candidates returned from Threads crawler for @{username}.")
            continue
            
        # Dedup & Persist
        new_count = 0
        for raw_art in candidates:
            link = raw_art["link"]
            
            # Fast check duplicate link
            existing = await db.articles.find_one({"link": link}, {"_id": 1})
            if existing:
                continue
                
            article = ArticleInDB(
                **raw_art,
                is_duplicate=False,
                duplicate_of_title=None
            )
            
            try:
                await db.articles.insert_one(article.model_dump(by_alias=True, exclude={'id'}))
                new_count += 1
                # Prompt broadcasting new article directly for critical trending socials
                await broadcast_new_article(article.model_dump())
            except DuplicateKeyError:
                pass
            except Exception as e:
                 logger.error(f"Failed inserting Threads article from @{username}: {e}")
                 
        logger.info(f"Threads aggregation for @{username} completed. Inserted {new_count} new articles.")

