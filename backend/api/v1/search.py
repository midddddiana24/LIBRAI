from typing import Literal
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.services.catalog_service import search_books
router=APIRouter(prefix="/search",tags=["Search"])
@router.get("/books")
def search(q:str|None=None,category:str|None=None,author:str|None=None,available_only:bool=False,publication_year:int|None=None,sort:Literal["title","newest","availability"]="title",offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db)):
    items,total=search_books(db,q,category,author,available_only,publication_year,offset,limit,sort=sort);return {"items":items,"total":total}
