from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from backend.core.database import get_db
from backend.core.security import get_current_admin, get_optional_admin, verify_kiosk_grant
from backend.models.entities import Admin, BookCopy, Borrowing, Fine
from backend.schemas.api import FinePaymentRequest
from backend.services.fine_service import fine_dict, mark_fine_paid

router = APIRouter(prefix="/fines", tags=["Fines"])


@router.get("")
def list_(user_id: int | None = None, status: str | None = None, verification_token: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), admin: Admin | None = Depends(get_optional_admin), db: Session = Depends(get_db)):
    if user_id and not admin:
        verify_kiosk_grant(verification_token, user_id)
    elif not admin:
        from fastapi import HTTPException
        raise HTTPException(401, "Admin authentication or a matching user verification token is required.")
    stmt = select(Fine).options(joinedload(Fine.borrowing).joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).order_by(Fine.assessed_at.desc())
    if user_id:
        stmt = stmt.where(Fine.user_id == user_id)
    if status:
        stmt = stmt.where(Fine.status == status.upper())
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = [fine_dict(x) for x in db.scalars(stmt.offset(offset).limit(limit)).unique()]
    return {"items": items, "total": total}


@router.post("/{fine_id}/pay")
def pay(fine_id: int, payload: FinePaymentRequest, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    return fine_dict(mark_fine_paid(db, fine_id, admin, payload.note))
