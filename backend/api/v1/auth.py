from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import create_access_token, get_current_admin, get_token_payload, verify_password
from backend.models.entities import Admin, RevokedToken
from backend.schemas.api import LoginRequest
from backend.services.audit_service import audit

router=APIRouter(prefix="/auth",tags=["Authentication"])

@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session=Depends(get_db)):
    admin=db.scalar(select(Admin).where(or_(Admin.username==payload.username,Admin.email==payload.username)))
    if not admin or not admin.is_active or not verify_password(payload.password,admin.password_hash): raise HTTPException(status_code=401,detail="Invalid credentials.")
    token,expires,_=create_access_token(admin);audit(db,"ADMIN_LOGIN","admin",admin.id,admin=admin,details={"ip":request.client.host if request.client else None});db.commit()
    return {"access_token":token,"token_type":"bearer","expires_at":expires,"user":{"id":admin.id,"name":admin.username,"username":admin.username,"email":admin.email,"role":admin.role}}

@router.get("/me")
def me(admin: Admin=Depends(get_current_admin)):return {"id":admin.id,"name":admin.username,"username":admin.username,"email":admin.email,"role":admin.role}

@router.post("/logout")
def logout(payload:dict=Depends(get_token_payload),admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    db.add(RevokedToken(jti=payload["jti"],expires_at=datetime.fromtimestamp(payload["exp"],tz=timezone.utc)));audit(db,"ADMIN_LOGOUT","admin",admin.id,admin=admin);db.commit();return {"message":"Logged out."}
