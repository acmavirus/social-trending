from fastapi import APIRouter, Body
from app.database import get_db
from app.models import NotificationSettings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

SETTINGS_DOC_ID = "global_config"

@router.get("/", response_model=NotificationSettings)
async def get_settings():
    db = get_db()
    doc = await db.settings.find_one({"_id": SETTINGS_DOC_ID})
    if not doc:
        return NotificationSettings()
    
    # Clean up internal id before matching response model
    doc.pop("_id", None)
    return NotificationSettings(**doc)

@router.put("/", response_model=NotificationSettings)
async def update_settings(settings: NotificationSettings):
    db = get_db()
    await db.settings.update_one(
        {"_id": SETTINGS_DOC_ID},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return settings
