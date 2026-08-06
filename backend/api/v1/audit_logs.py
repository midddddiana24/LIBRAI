from fastapi import APIRouter,Depends,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin
from backend.models.entities import Admin,AuditLog
router=APIRouter(prefix="/audit-logs",tags=["Audit"])
@router.get("")
def list_(action:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    stmt=select(AuditLog)
    if action:stmt=stmt.where(AuditLog.action==action)
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0;items=[{"id":x.id,"admin_id":x.admin_id,"actor_type":x.actor_type,"actor_id":x.actor_id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"details":x.details,"created_at":x.created_at} for x in db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit))];return {"items":items,"total":total}
