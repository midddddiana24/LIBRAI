from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin
from backend.models.entities import Admin,Category
from backend.services.audit_service import audit
router=APIRouter(prefix="/categories",tags=["Categories"])
class CategoryCreate(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    description:str|None=None
@router.get("")
def list_(db:Session=Depends(get_db)):return [{"id":x.id,"name":x.name,"description":x.description} for x in db.scalars(select(Category).order_by(Category.name))]
@router.post("",status_code=201)
def create(payload:CategoryCreate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    if db.scalar(select(Category).where(Category.name.ilike(payload.name))):raise HTTPException(409,"Category already exists.")
    item=Category(**payload.model_dump());db.add(item);db.flush();audit(db,"CATEGORY_CREATED","category",item.id,admin=admin);db.commit();return {"id":item.id,"name":item.name,"description":item.description}
