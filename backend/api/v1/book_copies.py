from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin
from backend.models.entities import Admin,BookCopy,Borrowing,BorrowingStatus,CopyStatus
from backend.schemas.api import CopyUpdate
from backend.services.audit_service import audit
router=APIRouter(prefix="/book-copies",tags=["Book Copies"])
@router.put("/{copy_id}")
def update(copy_id:int,payload:CopyUpdate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    copy=db.get(BookCopy,copy_id)
    if not copy:raise HTTPException(404,"Book copy not found.")
    if payload.status in {CopyStatus.BORROWED,CopyStatus.RESERVED}:
        raise HTTPException(409,"Borrowed and reserved states are controlled by circulation transactions.")
    if payload.status==CopyStatus.AVAILABLE and copy.book.is_archived:
        raise HTTPException(409,"Restore the catalog title before making this copy available.")
    if copy.status in {CopyStatus.BORROWED,CopyStatus.RESERVED} and payload.status not in {CopyStatus.BORROWED,CopyStatus.RESERVED}:
        active=db.query(Borrowing).filter(Borrowing.book_copy_id==copy.id,Borrowing.status.in_([BorrowingStatus.ACTIVE,BorrowingStatus.OVERDUE])).first()
        if active:raise HTTPException(409,"Return the active borrowing before changing this copy status.")
    copy.status=payload.status;audit(db,"BOOK_COPY_STATUS_CHANGED","book_copy",copy.id,admin=admin,details={"status":payload.status});db.commit();return {"id":copy.id,"book_copy_id":copy.id,"accession_number":copy.accession_number,"status":copy.status}
