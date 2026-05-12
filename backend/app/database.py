from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}")
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
    db_instance.db = db_instance.client[settings.DB_NAME]
    
    # Create indexes
    await db_instance.db.articles.create_index("link", unique=True)
    await db_instance.db.articles.create_index([("published_at", -1)])
    
    await db_instance.db.sources.create_index("url", unique=True)
    
    # Bootstrap initial feeds from config if collection empty
    count = await db_instance.db.sources.count_documents({})
    if count == 0:
        from app.models import FeedSourceInDB
        logger.info("Bootstrapping initial RSS feeds into database...")
        for feed in settings.RSS_FEEDS:
            source = FeedSourceInDB(**feed)
            try:
                await db_instance.db.sources.insert_one(source.model_dump(by_alias=True, exclude={'id'}))
            except Exception as e:
                logger.error(f"Failed to bootstrap {feed['name']}: {e}")
                
    logger.info("Connected to MongoDB and initialized indexes.")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection")
    if db_instance.client:
        db_instance.client.close()

def get_db():
    return db_instance.db
