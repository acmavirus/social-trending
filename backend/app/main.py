import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import connect_to_mongo, close_mongo_connection
from app.config import settings
from app.services.rss_service import run_all_aggregations
from app.services.threads_service import run_threads_aggregation
from app.routes.news import router as news_router
from app.routes.sources import router as sources_router
from app.routes.settings import router as settings_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    
    # Initial run schedule
    scheduler.add_job(run_all_aggregations, 'interval', minutes=settings.RSS_POLL_INTERVAL_MINUTES, id='fetch_rss')
    # Poll threads slightly less frequently to be respectful, e.g., double interval or min 15 mins
    threads_interval = max(15, settings.RSS_POLL_INTERVAL_MINUTES * 2)
    scheduler.add_job(run_threads_aggregation, 'interval', minutes=threads_interval, id='fetch_threads')
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Trigger first aggregation task immediately in background
    import asyncio
    asyncio.create_task(run_all_aggregations())
    asyncio.create_task(run_threads_aggregation())
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    await close_mongo_connection()

app = FastAPI(
    title="Social Trending RSS Aggregator",
    description="Aggregates news from various RSS feeds",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router)
app.include_router(sources_router)
app.include_router(settings_router)

@app.get("/")
async def root():
    return {"message": "Social Trending API is running", "status": "healthy"}

@app.post("/api/trigger-aggregation", tags=["Admin"])
async def trigger_aggregation():
    import asyncio
    asyncio.create_task(run_all_aggregations())
    asyncio.create_task(run_threads_aggregation())
    return {"message": "Aggregation triggered successfully"}
