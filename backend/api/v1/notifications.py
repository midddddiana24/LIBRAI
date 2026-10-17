from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_optional_admin,verify_kiosk_grant
from backend.models.entities import Admin,EmailDelivery,Notification
from backend.schemas.api import NotificationReadRequest
from backend.services.audit_service import audit
from backend.core.config import settings
from backend.scripts.email_worker import configured
from backend.services.email_dispatch import deliver_one
router=APIRouter(prefix="/notifications",tags=["Notifications"])
@router.get("/admin/email-status")
def email_status(admin:Admin=Depends(get_optional_admin)):
    if not admin:raise HTTPException(401,"Admin authentication required.")
    return {"smtp_configured":all((settings.smtp_host,settings.smtp_username,settings.smtp_password,settings.smtp_from)),"transport":settings.email_transport,"email_configured":bool(configured()),"autosend_enabled":settings.email_autosend_enabled,"delivery_mode":"API polling while awake if enabled, or separate worker. Configuration is not a delivery test."}

@router.post("/admin/email-deliveries/{delivery_id}/send",status_code=202)
def send_email(delivery_id:int,tasks:BackgroundTasks,admin:Admin=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if not admin:raise HTTPException(401,"Admin authentication required.")
    item=db.get(EmailDelivery,delivery_id)
    if not item:raise HTTPException(404,"Email not found.")
    if item.status!="PENDING":raise HTTPException(409,"Only pending emails can be dispatched. Retry a failed email first.")
    if not configured():raise HTTPException(503,"Email delivery is not configured on the API. Configure the Gmail sender first.")
    audit(db,"EMAIL_SEND_REQUESTED","email_delivery",item.id,admin=admin);db.commit()
    tasks.add_task(deliver_one,item.id)
    return {"message":"Delivery requested for this email only. Refresh its status, then check the recipient inbox."}

@router.post("/admin/email-deliveries/{delivery_id}/retry",status_code=202)
def retry_email(delivery_id:int,admin:Admin=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if not admin:raise HTTPException(401,"Admin authentication required.")
    item=db.scalar(select(EmailDelivery).where(EmailDelivery.id==delivery_id).with_for_update())
    if not item:raise HTTPException(404,"Email not found.")
    if item.status!="FAILED":raise HTTPException(409,"Only failed emails can be retried.")
    item.status="PENDING";item.error=None
    audit(db,"EMAIL_RETRY_QUEUED","email_delivery",item.id,admin=admin)
    db.commit()
    return {"message":"Email queued for retry. Use Send now or enabled automatic delivery."}
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
