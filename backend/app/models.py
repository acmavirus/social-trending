from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler=None):
        field_schema.update(type="string")
        return field_schema

class ArticleBase(BaseModel):
    title: str
    link: str
    summary: str
    content_snippet: Optional[str] = None
    published_at: datetime
    source_name: str
    category: str
    image_url: Optional[str] = None

class ArticleInDB(ArticleBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notified_discord: bool = False
    notified_telegram: bool = False
    is_duplicate: bool = False
    duplicate_of_title: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ArticleResponse(ArticleBase):
    id: str
    is_duplicate: bool = False
    duplicate_of_title: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True
    )

class FeedSourceBase(BaseModel):
    name: str
    url: str
    category: str = "General"
    is_active: bool = True

class FeedSourceInDB(FeedSourceBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_fetched_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class FeedSourceResponse(FeedSourceBase):
    id: str
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class NotificationSettings(BaseModel):
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # AI Feature Settings
    gemini_api_key: str = ""
    ai_deduplication_enabled: bool = False

class SocialSourceBase(BaseModel):
    platform: str = "Threads"
    username: str
    is_active: bool = True

class SocialSourceInDB(SocialSourceBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class SocialSourceResponse(SocialSourceBase):
    id: str
    
    model_config = ConfigDict(
        populate_by_name=True
    )

