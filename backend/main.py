from __future__ import annotations
import logging,time
from collections import defaultdict,deque
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from backend.api.v1.router import api_router
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.core.exceptions import install_exception_handlers
from backend.core.logging import configure_logging

configure_logging();logger=logging.getLogger(__name__)
app=FastAPI(title="LIBRAI API",version="1.0.0",description="Authoritative library kiosk backend",docs_url="/docs",redoc_url="/redoc")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
install_exception_handlers(app);app.include_router(api_router,prefix="/api/v1")
__import__("pathlib").Path("generated/covers").mkdir(parents=True,exist_ok=True)
# Only catalog covers are public. Reports, QR sheets and user photos live under
# generated/ too, but must only be served by their signed download endpoints.
app.mount("/files/covers",StaticFiles(directory="generated/covers"),name="book-covers")

requests_by_ip:dict[str,deque]=defaultdict(deque)
@app.middleware("http")
async def security_and_logging(request:Request,call_next):
    start=time.perf_counter();client=request.client.host if request.client else "unknown"
    if request.url.path in {"/api/v1/auth/login","/api/v1/ai/search","/api/v1/ai/feedback","/api/v1/qr/decode-image"}:
        now=time.monotonic();bucket=requests_by_ip[f"{client}:{request.url.path}"]
        while bucket and now-bucket[0]>60:bucket.popleft()
        if len(bucket)>=30:return JSONResponse(status_code=429,content={"detail":"Too many requests. Try again later."})
        bucket.append(now)
    content_length=request.headers.get("content-length")
    try:too_large=bool(content_length and int(content_length)>settings.max_upload_bytes)
    except ValueError:too_large=False
    if too_large:return JSONResponse(status_code=413,content={"detail":"Request body is too large."})
    response=await call_next(request);logger.info("request method=%s path=%s status=%s duration_ms=%.1f",request.method,request.url.path,response.status_code,(time.perf_counter()-start)*1000);return response

@app.get("/health",tags=["System"])
def health():
    with SessionLocal() as db:db.execute(text("SELECT 1"))
    return {"status":"healthy","service":"librai-api","version":"1.0.0"}

@app.get("/api/v1/health",include_in_schema=False)
def api_health():return health()
