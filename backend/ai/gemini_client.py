from __future__ import annotations
import json, logging
import httpx
from pydantic import BaseModel, Field, ValidationError
from backend.core.config import settings

logger = logging.getLogger(__name__)


class RankedBook(BaseModel):
    book_id: int
    reason: str = Field(max_length=500)


class GeminiRanking(BaseModel):
    message: str = Field(max_length=1000)
    recommendations: list[RankedBook]


class GeminiClient:
    def rank(self, query: str, candidates: list[dict]) -> GeminiRanking | None:
        if not settings.gemini_api_key or not candidates: return None
        safe = [{"book_id": b["id"], "title": b["title"], "author": b["author"], "category": b.get("category"), "description": b.get("description"), "keywords": b.get("keywords", []), "available_copies": b.get("available_copies"), "shelf_location": b.get("shelf_location")} for b in candidates]
        prompt = "Only recommend books from the supplied library catalog. Never invent titles or IDs. Return strict JSON with message and recommendations [{book_id, reason}]. User query: " + query + "\nCatalog: " + json.dumps(safe)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        try:
            response = httpx.post(url, params={"key": settings.gemini_api_key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}, timeout=12)
            response.raise_for_status(); text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            parsed = GeminiRanking.model_validate_json(text)
            allowed = {b["id"] for b in candidates}; parsed.recommendations = [r for r in parsed.recommendations if r.book_id in allowed]
            return parsed if parsed.recommendations else None
        except (httpx.HTTPError, KeyError, IndexError, ValidationError, json.JSONDecodeError) as exc:
            logger.warning("Gemini ranking unavailable: %s", type(exc).__name__)
            return None


gemini_client = GeminiClient()
