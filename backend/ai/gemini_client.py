from __future__ import annotations
import base64, json, logging, re, time
import httpx
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from backend.core.config import settings

logger = logging.getLogger(__name__)
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class RankedBook(BaseModel):
    book_id: int
    reason: str = Field(max_length=500)


class GeminiRanking(BaseModel):
    message: str = Field(max_length=1000)
    recommendations: list[RankedBook]


class GeminiClient:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, GeminiRanking]] = {}

    def _parse_ranking(self, text: str) -> GeminiRanking:
        cleaned = text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            cleaned = fenced.group(1).strip()
        return GeminiRanking.model_validate_json(cleaned)

    def rank(self, query: str, candidates: list[dict]) -> GeminiRanking | None:
        if not candidates: return None
        if settings.tokenrouter_api_key:
            return self._rank_tokenrouter(query, candidates)
        if not settings.gemini_api_key: return None
        safe = [{"book_id": b["id"], "title": b["title"], "author": b["author"], "category": b.get("category"), "description": b.get("description"), "keywords": b.get("keywords", []), "available_copies": b.get("available_copies"), "shelf_location": b.get("shelf_location")} for b in candidates]
        cache_key = json.dumps({"query": query.strip().lower(), "catalog": safe}, sort_keys=True, default=str)
        cached = self._cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        if cached:
            self._cache.pop(cache_key, None)
        prompt = "Only recommend books from the supplied library catalog. Never invent titles or IDs. Return strict JSON with message and recommendations [{book_id, reason}]. User query: " + query + "\nCatalog: " + json.dumps(safe)
        url = GEMINI_ENDPOINT.format(model=settings.gemini_model)
        request = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
        for attempt in range(settings.gemini_retry_count + 1):
            try:
                response = httpx.post(url, params={"key": settings.gemini_api_key}, json=request, timeout=settings.gemini_timeout_seconds)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                parsed = self._parse_ranking(text)
                allowed = {b["id"] for b in candidates}; parsed.recommendations = [r for r in parsed.recommendations if r.book_id in allowed]
                if not parsed.recommendations: return None
                self._cache[cache_key] = (time.monotonic() + settings.gemini_cache_seconds, parsed)
                if len(self._cache) > 256:
                    self._cache.pop(next(iter(self._cache)))
                return parsed
            except httpx.HTTPStatusError as exc:
                if attempt < settings.gemini_retry_count and (exc.response.status_code == 429 or exc.response.status_code >= 500):
                    continue
                logger.warning("Gemini ranking unavailable: HTTP %s", exc.response.status_code)
                return None
            except (httpx.HTTPError, KeyError, IndexError, ValidationError, json.JSONDecodeError) as exc:
                logger.warning("Gemini ranking unavailable: %s", type(exc).__name__)
                return None
        return None

    def _rank_tokenrouter(self, query: str, candidates: list[dict]) -> GeminiRanking | None:
        """Rank catalog candidates with the configured TokenRouter model."""
        safe = [{"book_id": b["id"], "title": b["title"], "author": b["author"], "category": b.get("category"), "description": b.get("description"), "keywords": b.get("keywords", []), "available_copies": b.get("available_copies"), "shelf_location": b.get("shelf_location")} for b in candidates]
        prompt = "Only recommend books from the supplied library catalog. Never invent titles or IDs. Return strict JSON with message and recommendations [{book_id, reason}]. User query: " + query + "\nCatalog: " + json.dumps(safe)
        try:
            client = OpenAI(base_url=settings.tokenrouter_base_url, api_key=settings.tokenrouter_api_key, timeout=settings.gemini_timeout_seconds)
            response = client.chat.completions.create(
                model=settings.tokenrouter_model,
                messages=[{"role": "system", "content": "You are LIBRAI's catalog recommendation assistant."}, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            parsed = self._parse_ranking(content)
            allowed = {b["id"] for b in candidates}
            parsed.recommendations = [r for r in parsed.recommendations if r.book_id in allowed]
            return parsed if parsed.recommendations else None
        except Exception as exc:
            logger.warning("TokenRouter ranking unavailable: %s", type(exc).__name__)
            return None

    def transcribe(self, audio: bytes, mime_type: str) -> str | None:
        if not settings.gemini_api_key or not audio:
            return None
        request = {
            "contents": [{"role": "user", "parts": [
                {"text": "Transcribe this library user's speech exactly. Return only the spoken words, with no quotation marks or explanation."},
                {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(audio).decode("ascii")}},
            ]}],
            "generationConfig": {"temperature": 0.0},
        }
        url = GEMINI_ENDPOINT.format(model=settings.gemini_model)
        try:
            response = httpx.post(url, params={"key": settings.gemini_api_key}, json=request, timeout=settings.gemini_timeout_seconds)
            response.raise_for_status()
            parts = response.json()["candidates"][0]["content"]["parts"]
            text = " ".join(str(part.get("text", "")) for part in parts).strip()
            return text or None
        except httpx.HTTPStatusError as exc:
            logger.warning("Gemini speech transcription unavailable: HTTP %s body=%s", exc.response.status_code, exc.response.text[:300])
            return None
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Gemini speech transcription unavailable: %s", type(exc).__name__)
            return None


gemini_client = GeminiClient()
