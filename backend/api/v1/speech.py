from fastapi import APIRouter,File,HTTPException,UploadFile
router=APIRouter(prefix="/speech",tags=["Speech"])
@router.post("/transcribe")
async def transcribe(audio:UploadFile=File(...)):
    if not audio.content_type or not audio.content_type.startswith("audio/"):raise HTTPException(415,"An audio file is required.")
    raise HTTPException(501,"Server speech transcription is not configured. Typed AI search remains available.")
