from fastapi import APIRouter, Depends, Query
from typing import List
from app.database import get_db
from app.models import ArticleResponse
from pymongo import DESCENDING

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("/", response_model=List[ArticleResponse])
async def get_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source: str = None,
    search: str = None
):
    db = get_db()
    
    # 1. Get names of all active sources (RSS and Social)
    active_rss_cursor = db.sources.find({"is_active": True}, {"name": 1})
    active_rss_names = [doc["name"] async for doc in active_rss_cursor]
    
    active_social_cursor = db.social_sources.find({"is_active": True}, {"username": 1})
    active_social_names = [f"Threads @{doc['username']}" async for doc in active_social_cursor]
    
    allowed_sources = active_rss_names + active_social_names
    
    # 2. Build Query
    query = {"is_duplicate": {"$ne": True}}
    
    # If a specific source is requested, make sure it's active
    if source:
        if source in allowed_sources:
            query["source_name"] = source
        else:
            # If requesting an inactive source, return empty list or just nothing
            return []
    else:
        # Only show articles from allowed sources
        query["source_name"] = {"$in": allowed_sources}

    if search:
        query["title"] = {"$regex": search, "$options": "i"}
        
    cursor = db.articles.find(query).sort("published_at", DESCENDING).skip(skip).limit(limit)
    
    articles = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        articles.append(ArticleResponse(**doc))
        
    return articles


@router.get("/sources")
async def get_sources():
    db = get_db()
    sources = await db.articles.distinct("source_name")
    return sources
