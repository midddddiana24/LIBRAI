from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import make_qr_token
from backend.models.entities import User
from backend.schemas.api import RegistrationCreate
from backend.services.audit_service import audit

router = APIRouter(prefix="/registrations", tags=["Registration"])
ACKNOWLEDGEMENT = {"message": "Request received. Library staff will review your details. If you already have an account or request, ask staff for help. No borrowing access is granted until approval."}


@router.post("", status_code=202)
def request_registration(payload: RegistrationCreate, db: Session = Depends(get_db)):
    user = User(**payload.model_dump(), qr_token=make_qr_token("USR_QR"))
    db.add(user)
    try:
        db.flush()
        audit(db, "REGISTRATION_REQUESTED", "user", user.id, actor_type="KIOSK")
        db.commit()
    except IntegrityError:
        # Do not disclose existing members or overwrite their records on public requests.
        db.rollback()
    return ACKNOWLEDGEMENT
