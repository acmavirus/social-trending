from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.database import get_db
from app.models import FeedSourceBase, FeedSourceInDB, FeedSourceResponse
from pymongo.errors import DuplicateKeyError
from app.services.rss_service import run_all_aggregations
import asyncio

router = APIRouter(prefix="/api/sources", tags=["Sources"])

@router.get("/", response_model=List[FeedSourceResponse])
async def list_sources():
    db = get_db()
    cursor = db.sources.find()
    sources = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        sources.append(FeedSourceResponse(**doc))
    return sources

@router.post("/", response_model=FeedSourceResponse)
async def add_source(source: FeedSourceBase):
    db = get_db()
    new_source = FeedSourceInDB(**source.model_dump())
    
    try:
        result = await db.sources.insert_one(new_source.model_dump(by_alias=True, exclude={'id'}))
        inserted_id = result.inserted_id
        
        # Fetch standard representation
        doc = await db.sources.find_one({"_id": inserted_id})
        doc["id"] = str(doc["_id"])
        
        # Trigger an aggregation for the new source in the background
        asyncio.create_task(run_all_aggregations())
        
        return FeedSourceResponse(**doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Source with this URL already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{source_id}")
async def delete_source(source_id: str):
    from bson import ObjectId
    db = get_db()
    
    if not ObjectId.is_valid(source_id):
        raise HTTPException(status_code=400, detail="Invalid source ID")
        
    res = await db.sources.delete_one({"_id": ObjectId(source_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Source not found")
        
    return {"message": "Source deleted successfully"}
