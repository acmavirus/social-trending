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
    
    query = {}
    if source:
        query["source_name"] = source
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
        
    cursor = db.articles.find(query).sort("published_at", DESCENDING).skip(skip).limit(limit)
    
    articles = []
    async for doc in cursor:
        # Convert ObjectId to str for response model
        doc["id"] = str(doc["_id"])
        articles.append(ArticleResponse(**doc))
        
    return articles

@router.get("/sources")
async def get_sources():
    db = get_db()
    sources = await db.articles.distinct("source_name")
    return sources
