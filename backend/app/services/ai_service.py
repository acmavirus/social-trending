import logging
import google.generativeai as genai
from typing import List
import json
import re
from app.models import ArticleInDB
from app.services.notifier_service import get_active_settings

logger = logging.getLogger(__name__)

async def analyze_batch_duplicates(candidates: List[dict], recent_articles: List[dict]) -> dict:
    """
    Uses Gemini to determine which candidates are reporting the same actual news event as
    any piece in the recent_articles list.
    Returns a mapping of candidate_link -> duplicate_of_title (or None).
    """
    if not candidates:
        return {}
        
    settings = await get_active_settings()
    if not settings or not settings.ai_deduplication_enabled or not settings.gemini_api_key:
        return {}
        
    try:
        genai.configure(api_key=settings.gemini_api_key)
        # Using fast model for cost and speed
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare short representations to save context
        recent_txt = "\n".join([f"- Title: {a['title']}" for a in recent_articles[:30]])
        
        candidate_list = []
        for i, c in enumerate(candidates):
            candidate_list.append({
                "idx": i,
                "title": c.get("title", ""),
                "summary": c.get("content_snippet", c.get("summary", ""))[:100]
            })
            
        prompt = f"""
TASK: Identify duplicate news events.
Different agencies report the same news with different titles. If a candidate article reports THE SAME EVENT as any title in the reference list below, it is a DUPLICATE.

### REFERENCE RECENT NEWS TITLES:
{recent_txt}

### NEW CANDIDATE ARTICLES TO CHECK:
{json.dumps(candidate_list, ensure_ascii=False)}

OUTPUT FORMAT: Valid JSON array of objects exactly: [{{"idx": number, "is_duplicate": boolean, "matching_title": "The reference title if duplicate, else null"}}].
Be conservative. Only mark as true if they describe the exact same global/local event occurring at the same time. Return JSON ONLY without markdown.
"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Safely clean markdown formatting if Gemini included it
        if "```" in text:
            text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
            
        results = json.loads(text)
        
        duplicates_map = {}
        for res in results:
            idx = res.get("idx")
            if idx is not None and idx < len(candidates):
                link = candidates[idx]["link"]
                if res.get("is_duplicate", False):
                    duplicates_map[link] = res.get("matching_title", "Previous Report")
        
        logger.info(f"AI checked {len(candidates)} items. Identified {len(duplicates_map)} duplicates.")
        return duplicates_map
        
    except Exception as e:
        logger.error(f"Gemini deduplication failure: {e}")
        return {}
