import httpx
import logging
from app.database import get_db
from app.models import ArticleInDB, NotificationSettings

logger = logging.getLogger(__name__)

SETTINGS_DOC_ID = "global_config"

async def get_active_settings():
    db = get_db()
    if db is None:
        return None
    doc = await db.settings.find_one({"_id": SETTINGS_DOC_ID})
    if not doc:
        return None
    return NotificationSettings(**doc)

async def notify_discord(article: ArticleInDB, webhook_url: str):
    payload = {
        "embeds": [{
            "title": article.title,
            "url": article.link,
            "description": article.content_snippet or article.summary[:250] + "...",
            "color": 5814783,
            "footer": {
                "text": f"Source: {article.source_name} | {article.category}"
            }
        }]
    }
    if article.image_url:
        payload["embeds"][0]["image"] = {"url": article.image_url}
        
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(webhook_url, json=payload, timeout=10.0)
            r.raise_for_status()
    except Exception as e:
        logger.error(f"Failed Discord Notify: {e}")

async def notify_telegram(article: ArticleInDB, bot_token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    text = (
        f"🔥 *{article.title}*\n\n"
        f"📰 Nguồn: _{article.source_name}_\n"
        f"🔗 Link: [Chi tiết]({article.link})\n"
    )
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, timeout=10.0)
            r.raise_for_status()
    except Exception as e:
        logger.error(f"Failed Telegram Notify: {e}")

async def process_pending_notifications(limit: int = 20):
    db = get_db()
    if db is None:
        return
        
    settings = await get_active_settings()
    if not settings:
        return

    # Stop if both disabled
    if not settings.discord_enabled and not settings.telegram_enabled:
        return
        
    # Construct specific query based on active networks
    conditions = []
    if settings.discord_enabled and settings.discord_webhook_url:
        conditions.append({"notified_discord": {"$ne": True}})
    if settings.telegram_enabled and settings.telegram_bot_token and settings.telegram_chat_id:
        conditions.append({"notified_telegram": {"$ne": True}})
        
    if not conditions:
        return

    # Skip AI duplicates and limit to very recent ones
    full_query = {
        "$and": [
            {"$or": conditions},
            {"is_duplicate": {"$ne": True}}
        ]
    }

    from pymongo import DESCENDING
    cursor = db.articles.find(full_query).sort("published_at", DESCENDING).limit(limit)
    
    async for doc in cursor:
        # Convert to full object
        article = ArticleInDB(**doc)
        article_id = doc["_id"]
        
        updates = {}
        
        # Handle Discord
        if settings.discord_enabled and not doc.get("notified_discord", False):
            try:
                await notify_discord(article, settings.discord_webhook_url)
                updates["notified_discord"] = True
            except Exception: pass
            
        # Handle Telegram
        if settings.telegram_enabled and not doc.get("notified_telegram", False):
            try:
                await notify_telegram(article, settings.telegram_bot_token, settings.telegram_chat_id)
                updates["notified_telegram"] = True
            except Exception: pass
            
        # Apply updates atomically back to DB
        if updates:
            await db.articles.update_one({"_id": article_id}, {"$set": updates})

async def broadcast_new_article(article: ArticleInDB):
    # Instead of just broadcasting one, we just kick off the queue processing
    import asyncio
    asyncio.create_task(process_pending_notifications(limit=10))
