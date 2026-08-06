from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session,joinedload
from backend.core.database import get_db
from backend.core.security import get_current_admin,get_optional_admin,verify_book_grant,verify_kiosk_grant
from backend.models.entities import Admin,BookCopy,Borrowing,BorrowingStatus
from backend.schemas.api import BorrowCreate,RenewRequest
from backend.services.borrowing_service import borrow_book,renew_borrowing
from backend.services.policy_service import max_renewals
router=APIRouter(prefix="/borrowings",tags=["Borrowings"])
def receipt(x,db):
    limit=max_renewals(db);due=x.due_at if x.due_at.tzinfo else x.due_at.replace(tzinfo=timezone.utc);return {"id":x.id,"transaction_id":f"BOR-{x.id:08d}","user_id":x.user_id,"book_copy_id":x.book_copy_id,"book_title":x.book_copy.book.title,"borrowed_at":x.borrowed_at,"due_at":x.due_at,"returned_at":x.returned_at,"status":x.status.lower(),"renewal_count":x.renewal_count,"max_renewals":limit,"can_renew":x.status==BorrowingStatus.ACTIVE and due>=datetime.now(timezone.utc) and x.renewal_count<limit}
@router.post("",status_code=201)
def create(payload:BorrowCreate,db:Session=Depends(get_db)):
    verify_kiosk_grant(payload.user_verification_token,payload.user_id);verify_book_grant(payload.book_verification_token,payload.book_copy_id);return receipt(borrow_book(db,payload.user_id,payload.book_copy_id,payload.kiosk_id),db)

@router.post("/{borrowing_id}/renew")
def renew(borrowing_id:int,payload:RenewRequest,db:Session=Depends(get_db)):
    verify_kiosk_grant(payload.user_verification_token,payload.user_id)
    return receipt(renew_borrowing(db,borrowing_id,payload.user_id),db)
@router.get("")
def list_(user_id:int|None=None,verification_token:str|None=None,status:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if user_id and not admin:verify_kiosk_grant(verification_token,user_id)
    elif not admin:raise HTTPException(401,"Authentication required.")
    stmt=select(Borrowing).options(joinedload(Borrowing.book_copy).joinedload(BookCopy.book))
    if user_id:stmt=stmt.where(Borrowing.user_id==user_id)
    if status:stmt=stmt.where(Borrowing.status==status.upper())
    total=db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0;return {"items":[receipt(x,db) for x in db.scalars(stmt.order_by(Borrowing.borrowed_at.desc()).offset(offset).limit(limit)).unique()],"total":total}
@router.get("/active/by-copy/{copy_id}")
def by_copy(copy_id:int,book_verification_token:str|None=None,db:Session=Depends(get_db)):
    verify_book_grant(book_verification_token,copy_id)
    x=db.scalar(select(Borrowing).options(joinedload(Borrowing.user),joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).where(Borrowing.book_copy_id==copy_id,Borrowing.status.in_([BorrowingStatus.ACTIVE,BorrowingStatus.OVERDUE])))
    if not x:raise HTTPException(404,"No active borrowing exists for this copy.")
    return {"id":x.id,"copy_id":copy_id,"book_title":x.book_copy.book.title,"user_name":x.user.display_name,"student_id":x.user.student_id,"due_at":x.due_at,"status":x.status.lower()}
@router.get("/{borrowing_id}")
def get_(borrowing_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    x=db.scalar(select(Borrowing).options(joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).where(Borrowing.id==borrowing_id))
    if not x:raise HTTPException(404,"Borrowing not found.")
    return receipt(x,db)
