from fastapi import APIRouter,File,HTTPException,UploadFile
from backend.ai.gemini_client import gemini_client
from backend.core.config import settings
router=APIRouter(prefix="/speech",tags=["Speech"])
@router.post("/transcribe")
async def transcribe(audio:UploadFile=File(...)):
    if not audio.content_type or not audio.content_type.startswith("audio/"):raise HTTPException(415,"An audio file is required.")
    content=await audio.read(settings.max_upload_bytes+1)
    if not content:raise HTTPException(422,"The audio recording is empty.")
    if len(content)>settings.max_upload_bytes:raise HTTPException(413,"The audio recording is too large.")
    if not settings.gemini_api_key:raise HTTPException(503,"Speech transcription requires GEMINI_API_KEY in the backend environment.")
    # Browsers and recorders commonly label WAV as audio/x-wav. Gemini accepts
    # the standard audio/wav MIME value more consistently.
    mime_type = "audio/wav" if audio.content_type in {"audio/x-wav", "audio/wave", "audio/vnd.wave"} else audio.content_type
    text=gemini_client.transcribe(content,mime_type)
    if not text:raise HTTPException(502,"The speech service could not transcribe that recording. Please try again.")
    return {"text":text}
