from io import BytesIO
import base64, re, qrcode
import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import create_book_grant, create_kiosk_grant, create_qr_download_grant, get_current_admin, make_qr_token, verify_qr_download_grant
from backend.models.entities import Admin, BookCopy, Borrowing, BorrowingStatus, CopyStatus, User
from backend.schemas.api import QRVerifyRequest
from backend.services.audit_service import audit
from backend.services.policy_service import borrowing_limit
from backend.services.serialization import user_safe_dict

router=APIRouter(tags=["QR"])
def qr_png(token):
    image=qrcode.make(token);buf=BytesIO();image.save(buf,format="PNG");return buf.getvalue()
def qr_data(token):return "data:image/png;base64,"+base64.b64encode(qr_png(token)).decode()
def qr_admin_payload(entity_type:str,entity_id:int,token:str):
    ticket=create_qr_download_grant(entity_type,entity_id)
    id_key="user_id" if entity_type=="user" else "book_copy_id"
    return {id_key:entity_id,"qr_image":qr_data(token),"download_url":f"/qr/download/{ticket}"}

@router.post("/qr/decode-image")
async def decode_qr_image(file:UploadFile=File(...)):
    """Decode one QR image without storing it or trusting its contents."""
    if file.content_type not in {"image/jpeg","image/png","image/webp"}:
        raise HTTPException(415,"QR photo must be JPEG, PNG, or WebP.")
    content=await file.read(settings.max_upload_bytes+1)
    if not content:raise HTTPException(422,"The selected QR photo is empty.")
    if len(content)>settings.max_upload_bytes:raise HTTPException(413,"QR photo is too large.")
    image=cv2.imdecode(np.frombuffer(content,dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None:raise HTTPException(422,"The selected file is not a valid image.")
    height,width=image.shape[:2]
    if height*width>36_000_000:raise HTTPException(422,"QR photo dimensions are too large.")
    token,points,_=cv2.QRCodeDetector().detectAndDecode(image)
    token=token.strip()
    if points is None or not token:raise HTTPException(422,"No readable QR code was found. Move closer and take another photo.")
    if len(token)>300:raise HTTPException(422,"The decoded QR value is too long.")
    return {"token":token}

@router.post("/qr/verify-user")
def verify_user(payload:QRVerifyRequest,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.qr_token==payload.resolved_token))
    if not user:raise HTTPException(status_code=404,detail="Invalid user QR code.")
    data=user_safe_dict(db,user,borrowing_limit(db));data["verification_token"]=create_kiosk_grant(user.id);return data

@router.post("/qr/verify-book")
def verify_book(payload:QRVerifyRequest,db:Session=Depends(get_db)):
    copy=db.scalar(select(BookCopy).options(joinedload(BookCopy.book)).where(BookCopy.qr_token==payload.resolved_token))
    if not copy:raise HTTPException(status_code=404,detail="Invalid book QR code.")
    b=copy.book;return {"id":copy.id,"book_copy_id":copy.id,"copy_id":copy.accession_number,"accession_number":copy.accession_number,"book_id":b.id,"title":b.title,"author":b.author,"category":b.category.name,"shelf_location":b.shelf_location,"available":copy.status==CopyStatus.AVAILABLE,"availability":copy.status,"can_borrow":copy.status==CopyStatus.AVAILABLE,"cover_url":b.cover_image,"verification_token":create_book_grant(copy.id)}

@router.post("/users/{user_id}/qr")
def rotate_user_qr(user_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    user.qr_token=make_qr_token("USR_QR");audit(db,"USER_QR_ROTATED","user",user.id,admin=admin);db.commit();return qr_admin_payload("user",user.id,user.qr_token)

@router.get("/users/{user_id}/qr")
def get_user_qr(user_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    return qr_admin_payload("user",user.id,user.qr_token)

@router.post("/book-copies/{copy_id}/qr")
def rotate_copy_qr(copy_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    copy=db.get(BookCopy,copy_id)
    if not copy:raise HTTPException(404,"Book copy not found.")
    copy.qr_token=make_qr_token("BOOK_QR");audit(db,"BOOK_COPY_QR_ROTATED","book_copy",copy.id,admin=admin);db.commit();return qr_admin_payload("book_copy",copy.id,copy.qr_token)

@router.get("/book-copies/{copy_id}/qr")
def get_copy_qr(copy_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    copy=db.get(BookCopy,copy_id)
    if not copy:raise HTTPException(404,"Book copy not found.")
    return qr_admin_payload("book_copy",copy.id,copy.qr_token)

@router.get("/qr/download/{ticket}",response_class=Response)
def download_qr(ticket:str,db:Session=Depends(get_db)):
    entity_type,entity_id=verify_qr_download_grant(ticket)
    if entity_type=="user":
        entity=db.get(User,entity_id)
        identifier=entity.student_id if entity else ""
    else:
        entity=db.get(BookCopy,entity_id)
        identifier=entity.accession_number if entity else ""
    if not entity:raise HTTPException(404,"QR owner not found.")
    safe_identifier=re.sub(r"[^A-Za-z0-9._-]+","-",identifier).strip("-") or str(entity_id)
    headers={"Content-Disposition":f'attachment; filename="LIBRAI-{safe_identifier}-QR.png"',"Cache-Control":"no-store"}
    return Response(content=qr_png(entity.qr_token),media_type="image/png",headers=headers)
