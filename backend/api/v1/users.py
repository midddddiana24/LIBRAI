from fastapi import APIRouter,Depends,File,HTTPException,Query,UploadFile
from typing import Literal
from sqlalchemy import func,or_,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import get_current_admin,make_qr_token,verify_user_photo_grant
from backend.models.entities import Admin,User
from backend.schemas.api import UserCreate,UserUpdate
from backend.services.audit_service import audit
from backend.services.policy_service import borrowing_limit
from backend.services.serialization import user_admin_dict
from backend.services.media_service import private_user_photo_path,store_image
from backend.services import object_storage
from backend.services.notification_service import queue_library_id

router=APIRouter(prefix="/users",tags=["Users"])

@router.get("/photo/{ticket}")
def user_photo(ticket:str,db:Session=Depends(get_db)):
    user_id=verify_user_photo_grant(ticket);user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    if not user.photo_image or not user.photo_image.startswith("private/users/") or ".." in user.photo_image.split("/"):
        raise HTTPException(404,"User photo not found.")
    path = f"generated/{user.photo_image}" if object_storage.enabled() else private_user_photo_path(user.photo_image)
    return object_storage.media_response(path,media_type="image/webp",headers={"Cache-Control":"private, max-age=300"})
@router.get("")
def list_users(q:str|None=None,status:Literal["ACTIVE","PENDING","INACTIVE","SUSPENDED"]|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    stmt=select(User)
    if status:stmt=stmt.where(User.status==status)
    if q:stmt=stmt.where(or_(User.student_id.ilike(f"%{q}%"),User.library_card_number.ilike(f"%{q}%"),User.first_name.ilike(f"%{q}%"),User.last_name.ilike(f"%{q}%")))
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0;items=[user_admin_dict(db,u,borrowing_limit(db)) for u in db.scalars(stmt.offset(offset).limit(limit))];return {"items":items,"total":total}
@router.post("",status_code=201)
def create_user(payload:UserCreate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=User(**payload.model_dump(),qr_token=make_qr_token("USR_QR"));db.add(user)
    try:
        db.flush()
        if user.status=="ACTIVE":queue_library_id(db,user)
        audit(db,"USER_CREATED","user",user.id,admin=admin);db.commit();return user_admin_dict(db,user,borrowing_limit(db))
    except IntegrityError:db.rollback();raise HTTPException(409,"Student ID, library card number, or email already exists.")
@router.get("/{user_id}")
def get_user(user_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    return user_admin_dict(db,user,borrowing_limit(db))
@router.put("/{user_id}")
def update_user(user_id:int,payload:UserUpdate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    previous_status=user.status
    for k,v in payload.model_dump(exclude_unset=True).items():setattr(user,k,v)
    try:
        action="REGISTRATION_APPROVED" if previous_status=="PENDING" and user.status=="ACTIVE" else "REGISTRATION_REJECTED" if previous_status=="PENDING" and user.status=="INACTIVE" else "USER_UPDATED"
        db.flush()
        if action=="REGISTRATION_APPROVED":queue_library_id(db,user)
        audit(db,action,"user",user.id,admin=admin,details={"fields":list(payload.model_fields_set)});db.commit();return user_admin_dict(db,user,borrowing_limit(db))
    except IntegrityError:db.rollback();raise HTTPException(409,"Library card number or email already exists.")

@router.post("/{user_id}/email-qr",status_code=202)
def email_qr(user_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    from backend.models.entities import EmailDelivery,Notification
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    if user.status!="ACTIVE" or not user.email:raise HTTPException(409,"An active account and registered email are required.")
    pending=db.scalar(select(EmailDelivery.id).join(Notification,EmailDelivery.notification_id==Notification.id).where(EmailDelivery.user_id==user.id,EmailDelivery.recipient==user.email,EmailDelivery.status=="PENDING",Notification.type=="LIBRARY_ID"))
    if not pending:
        queue_library_id(db,user)
        audit(db,"LIBRARY_ID_EMAIL_QUEUED","user",user.id,admin=admin)
        db.commit()
    return {"message":"Library ID email queued. Check Email deliveries for its status."}

@router.post("/{user_id}/photo")
async def upload_user_photo(user_id:int,file:UploadFile=File(...),admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    content=await file.read(settings.max_upload_bytes+1)
    user.photo_image=store_image(content,file.content_type,"users",user.id,user.photo_image)
    audit(db,"USER_PHOTO_UPDATED","user",user.id,admin=admin);db.commit()
    return user_admin_dict(db,user,borrowing_limit(db))
