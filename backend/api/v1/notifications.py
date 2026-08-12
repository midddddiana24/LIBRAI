from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_optional_admin,verify_kiosk_grant
from backend.models.entities import Admin,EmailDelivery,Notification
from backend.schemas.api import NotificationReadRequest
router=APIRouter(prefix="/notifications",tags=["Notifications"])
@router.get("/admin/email-deliveries")
def email_deliveries(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),status:str|None=None,_admin:Admin=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if not _admin: raise HTTPException(401,"Admin authentication required.")
    stmt=select(EmailDelivery).order_by(EmailDelivery.created_at.desc())
    if status: stmt=stmt.where(EmailDelivery.status==status.upper())
    total=db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items=[{"id":x.id,"recipient":x.recipient,"subject":x.subject,"status":x.status.lower(),"error":x.error,"created_at":x.created_at,"sent_at":x.sent_at} for x in db.scalars(stmt.offset(offset).limit(limit))]
    return {"items":items,"total":total}
@router.get("")
def list_(user_id:int,verification_token:str|None=None,admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if not admin:verify_kiosk_grant(verification_token,user_id)
    return [{"id":x.id,"type":x.type,"message":x.message,"is_read":x.is_read,"created_at":x.created_at} for x in db.scalars(select(Notification).where(Notification.user_id==user_id).order_by(Notification.created_at.desc()))]
@router.post("/{notification_id}/read")
def read(notification_id:int,payload:NotificationReadRequest,admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    item=db.get(Notification,notification_id)
    if not item:raise HTTPException(404,"Notification not found.")
    if not admin:verify_kiosk_grant(payload.verification_token,item.user_id)
    item.is_read=True;db.commit();return {"id":item.id,"is_read":True}
