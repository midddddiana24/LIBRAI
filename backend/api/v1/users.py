from fastapi import APIRouter,Depends,File,HTTPException,Query,UploadFile
from fastapi.responses import FileResponse
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

router=APIRouter(prefix="/users",tags=["Users"])

@router.get("/photo/{ticket}",response_class=FileResponse)
def user_photo(ticket:str,db:Session=Depends(get_db)):
    user_id=verify_user_photo_grant(ticket);user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    return FileResponse(private_user_photo_path(user.photo_image),media_type="image/webp",headers={"Cache-Control":"private, max-age=300"})
@router.get("")
def list_users(q:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    stmt=select(User)
    if q:stmt=stmt.where(or_(User.student_id.ilike(f"%{q}%"),User.first_name.ilike(f"%{q}%"),User.last_name.ilike(f"%{q}%")))
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0;items=[user_admin_dict(db,u,borrowing_limit(db)) for u in db.scalars(stmt.offset(offset).limit(limit))];return {"items":items,"total":total}
@router.post("",status_code=201)
def create_user(payload:UserCreate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=User(**payload.model_dump(),qr_token=make_qr_token("USR_QR"));db.add(user)
    try:db.flush();audit(db,"USER_CREATED","user",user.id,admin=admin);db.commit();return user_admin_dict(db,user,borrowing_limit(db))
    except IntegrityError:db.rollback();raise HTTPException(409,"Student ID or email already exists.")
@router.get("/{user_id}")
def get_user(user_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    return user_admin_dict(db,user,borrowing_limit(db))
@router.put("/{user_id}")
def update_user(user_id:int,payload:UserUpdate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    for k,v in payload.model_dump(exclude_unset=True).items():setattr(user,k,v)
    audit(db,"USER_UPDATED","user",user.id,admin=admin,details={"fields":list(payload.model_fields_set)});db.commit();return user_admin_dict(db,user,borrowing_limit(db))

@router.post("/{user_id}/photo")
async def upload_user_photo(user_id:int,file:UploadFile=File(...),admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found.")
    content=await file.read(settings.max_upload_bytes+1)
    user.photo_image=store_image(content,file.content_type,"users",user.id,user.photo_image)
    audit(db,"USER_PHOTO_UPDATED","user",user.id,admin=admin);db.commit()
    return user_admin_dict(db,user,borrowing_limit(db))
