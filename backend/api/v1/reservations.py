from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session,joinedload
from backend.core.database import get_db
from backend.core.security import get_current_admin,get_optional_admin,verify_kiosk_grant
from backend.models.entities import Admin,Reservation,ReservationStatus
from backend.schemas.api import ReservationCreate
from backend.services.audit_service import audit
from backend.services.reservation_service import create_reservation,expire_reservations
router=APIRouter(prefix="/reservations",tags=["Reservations"])
def item(db,x):
    position=db.scalar(select(func.count(Reservation.id)).where(Reservation.book_id==x.book_id,Reservation.status==ReservationStatus.ACTIVE,Reservation.reserved_at<=x.reserved_at)) if x.status==ReservationStatus.ACTIVE else None
    return {"id":x.id,"user_id":x.user_id,"user_name":x.user.display_name,"student_id":x.user.student_id,"course":x.user.course,"book_id":x.book_id,"book_title":x.book.title,"book_author":x.book.author,"cover_url":x.book.cover_image,"shelf_location":x.book.shelf_location,"status":x.status.lower(),"position":position,"reserved_at":x.reserved_at,"expected_available_at":x.expires_at}
@router.get("")
def list_(user_id:int|None=None,verification_token:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    expire_reservations(db)
    if user_id:verify_kiosk_grant(verification_token,user_id)
    elif not admin:raise HTTPException(401,"Authentication required.")
    stmt=select(Reservation).options(joinedload(Reservation.user),joinedload(Reservation.book)).order_by(Reservation.reserved_at)
    if user_id:stmt=stmt.where(Reservation.user_id==user_id)
    total=db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0;return {"items":[item(db,x) for x in db.scalars(stmt.offset(offset).limit(limit)).unique()],"total":total}
@router.post("",status_code=201)
def create(payload:ReservationCreate,db:Session=Depends(get_db)):
    verify_kiosk_grant(payload.user_verification_token,payload.user_id);x,position=create_reservation(db,payload.user_id,payload.book_id);return {**item(db,x),"position":position}
@router.delete("/{reservation_id}")
def cancel(reservation_id:int,verification_token:str|None=None,admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    x=db.get(Reservation,reservation_id)
    if not x:raise HTTPException(404,"Reservation not found.")
    if not admin:verify_kiosk_grant(verification_token,x.user_id)
    if x.status not in [ReservationStatus.ACTIVE,ReservationStatus.READY]:raise HTTPException(409,"Reservation cannot be cancelled.")
    x.status=ReservationStatus.CANCELLED;audit(db,"RESERVATION_CANCELLED","reservation",x.id,admin=admin,actor_type="ADMIN" if admin else "KIOSK",actor_id=admin.id if admin else x.user_id);db.commit();return {"id":x.id,"status":"cancelled"}
