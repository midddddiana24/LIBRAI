from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import require_super_admin
from backend.models.entities import Admin,SystemSetting
from backend.services.audit_service import audit
from backend.services.policy_service import DEFAULTS
router=APIRouter(prefix="/settings",tags=["Settings"])
def validated_value(key:str,raw) -> str:
    if key not in DEFAULTS:raise HTTPException(404,"Unsupported setting.")
    value=str(raw if raw is not None else "").strip()
    if key=="ALLOW_BORROW_WITH_OVERDUE":
        if value.lower() not in {"true","false"}:raise HTTPException(422,"Value must be true or false.")
        return value.lower()
    try:number=int(value)
    except ValueError:raise HTTPException(422,"Value must be a whole number.")
    minimum=0 if key=="MAX_RENEWALS" else 1
    if number<minimum:raise HTTPException(422,f"Value must be at least {minimum}.")
    return str(number)

@router.put("")
def update_all(payload:dict,admin:Admin=Depends(require_super_admin),db:Session=Depends(get_db)):
    values={key:validated_value(key,value) for key,value in payload.items()}
    if not values:raise HTTPException(422,"At least one setting is required.")
    for key,value in values.items():
        row=db.scalar(select(SystemSetting).where(SystemSetting.key==key))
        if not row:db.add(SystemSetting(key=key,value=value))
        else:row.value=value
        audit(db,"SETTING_CHANGED","system_setting",key,admin=admin,details={"value":value})
    db.commit();return {**DEFAULTS,**{x.key:x.value for x in db.scalars(select(SystemSetting))}}
@router.get("")
def list_(_admin:Admin=Depends(require_super_admin),db:Session=Depends(get_db)):
    stored={x.key:x.value for x in db.scalars(select(SystemSetting))};return {**DEFAULTS,**stored}
@router.put("/{key}")
def update(key:str,payload:dict,admin:Admin=Depends(require_super_admin),db:Session=Depends(get_db)):
    value=validated_value(key,payload.get("value"))
    row=db.scalar(select(SystemSetting).where(SystemSetting.key==key))
    if not row:row=SystemSetting(key=key,value=value);db.add(row)
    else:row.value=value
    audit(db,"SETTING_CHANGED","system_setting",key,admin=admin);db.commit();return {"key":key,"value":row.value}
