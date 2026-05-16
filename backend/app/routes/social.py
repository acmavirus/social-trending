from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.database import get_db
from app.models import SocialSourceBase, SocialSourceInDB, SocialSourceResponse
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

router = APIRouter(prefix="/api/social", tags=["Social"])

@router.get("/", response_model=List[SocialSourceResponse])
async def list_social_sources():
    db = get_db()
    cursor = db.social_sources.find()
    sources = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        sources.append(SocialSourceResponse(**doc))
    return sources

@router.post("/", response_model=SocialSourceResponse)
async def add_social_source(source: SocialSourceBase):
    db = get_db()
    new_source = SocialSourceInDB(**source.model_dump())
    
    # Check if username already exists for this platform
    existing = await db.social_sources.find_one({
        "platform": source.platform,
        "username": source.username
    })
    if existing:
        raise HTTPException(status_code=400, detail="This username is already being tracked")
        
    result = await db.social_sources.insert_one(new_source.model_dump(by_alias=True, exclude={'id'}))
    inserted_id = result.inserted_id
    
    doc = await db.social_sources.find_one({"_id": inserted_id})
    doc["id"] = str(doc["_id"])
    return SocialSourceResponse(**doc)

@router.patch("/{source_id}/toggle")
async def toggle_social_source(source_id: str, is_active: bool = Body(..., embed=True)):
    db = get_db()
    if not ObjectId.is_valid(source_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    res = await db.social_sources.update_one(
        {"_id": ObjectId(source_id)},
        {"$set": {"is_active": is_active}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Updated successfully"}

@router.delete("/{source_id}")
async def delete_social_source(source_id: str):
    db = get_db()
    if not ObjectId.is_valid(source_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    res = await db.social_sources.delete_one({"_id": ObjectId(source_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted successfully"}
