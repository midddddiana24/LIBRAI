from datetime import date,datetime,time,timezone
from io import StringIO
import csv
from fastapi import APIRouter,Depends,Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin
from backend.models.entities import Admin,AuditLog
router=APIRouter(prefix="/audit-logs",tags=["Audit"])
def _filtered(action,actor_type,actor_id,start_date,end_date):
    stmt=select(AuditLog)
    if action:stmt=stmt.where(AuditLog.action==action)
    if actor_type:stmt=stmt.where(AuditLog.actor_type==actor_type.upper())
    if actor_id:stmt=stmt.where(AuditLog.actor_id==actor_id)
    if start_date:stmt=stmt.where(AuditLog.created_at>=datetime.combine(start_date,time.min,tzinfo=timezone.utc))
    if end_date:stmt=stmt.where(AuditLog.created_at<datetime.combine(end_date,time.max,tzinfo=timezone.utc))
    return stmt

def _rows(db,stmt):
    return [{"id":x.id,"admin_id":x.admin_id,"actor_type":x.actor_type,"actor_id":x.actor_id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"details":x.details,"created_at":x.created_at} for x in db.scalars(stmt.order_by(AuditLog.created_at.desc()))]

@router.get("")
def list_(action:str|None=None,actor_type:str|None=None,actor_id:str|None=None,start_date:date|None=None,end_date:date|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    stmt=_filtered(action,actor_type,actor_id,start_date,end_date);total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0;return {"items":_rows(db,stmt.offset(offset).limit(limit)),"total":total}

@router.get("/export.csv")
def export_csv(action:str|None=None,actor_type:str|None=None,actor_id:str|None=None,start_date:date|None=None,end_date:date|None=None,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    output=StringIO();writer=csv.writer(output);writer.writerow(["id","admin_id","actor_type","actor_id","action","entity_type","entity_id","created_at","details"])
    for row in _rows(db,_filtered(action,actor_type,actor_id,start_date,end_date)):writer.writerow([row["id"],row["admin_id"],row["actor_type"],row["actor_id"],row["action"],row["entity_type"],row["entity_id"],row["created_at"],row["details"]])
    return StreamingResponse(iter([output.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=librai-audit-log.csv"})
