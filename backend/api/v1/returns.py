from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session,joinedload
from backend.core.database import get_db
from backend.core.security import get_current_admin,verify_book_grant
from backend.models.entities import Admin,BookCopy,Borrowing,BorrowingStatus
from backend.schemas.api import ReturnCreate
from backend.services.borrowing_service import return_book
router=APIRouter(prefix="/returns",tags=["Returns"])
@router.post("",status_code=201)
def create(payload:ReturnCreate,db:Session=Depends(get_db)):
    existing=db.get(Borrowing,payload.borrowing_id)
    if not existing:raise HTTPException(404,"Borrowing not found.")
    verify_book_grant(payload.book_verification_token,existing.book_copy_id);x,result=return_book(db,payload.borrowing_id);return {"id":x.id,"transaction_id":f"RET-{x.id:08d}","book_title":x.book_copy.book.title,"returned_at":x.returned_at,"return_status":result}
@router.get("")
def list_(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    stmt=select(Borrowing).options(joinedload(Borrowing.user),joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).where(Borrowing.status==BorrowingStatus.RETURNED);total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0;return {"items":[{"id":x.id,"book":x.book_copy.book.title,"user":x.user.display_name,"returned_at":x.returned_at,"status":"returned"} for x in db.scalars(stmt.offset(offset).limit(limit)).unique()],"total":total}
