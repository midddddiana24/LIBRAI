from fastapi import APIRouter,Depends,File,HTTPException,Query,UploadFile
from sqlalchemy import func,select
from sqlalchemy.orm import Session,joinedload
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import create_report_download_grant,get_current_admin,get_optional_admin,make_qr_token
from backend.models.entities import Admin,Book,BookCopy,CopyStatus,ReportJob
from backend.reports.qr_sheet import generate_book_qr_sheet
from backend.schemas.api import BookCreate,BookUpdate,CopiesCreate
from backend.services.audit_service import audit
from backend.services.catalog_service import get_or_create_category,search_books
from backend.services.serialization import book_dict
from backend.services.media_service import store_image

router=APIRouter(prefix="/books",tags=["Books"])
@router.get("")
def list_books(q:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),include_archived:bool=False,admin:Admin|None=Depends(get_optional_admin),db:Session=Depends(get_db)):
    if include_archived and not admin:raise HTTPException(403,"Admin access is required to include archived books.")
    if not include_archived:
        items,total=search_books(db,q=q,offset=offset,limit=limit);return {"items":items,"total":total}
    stmt=select(Book).options(joinedload(Book.category));total=db.scalar(select(func.count(Book.id))) or 0;return {"items":[book_dict(db,b) for b in db.scalars(stmt.offset(offset).limit(limit))],"total":total}
@router.post("",status_code=201)
def create_book(payload:BookCreate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    data=payload.model_dump(exclude={"category","category_id","initial_copy_count"});category=get_or_create_category(db,payload.category_id,payload.category);book=Book(**data,category_id=category.id);db.add(book);db.flush()
    copies=[]
    for index in range(payload.initial_copy_count):
        copy=BookCopy(book_id=book.id,accession_number=f"BK-{book.id:05d}-C{index+1:03d}",qr_token=make_qr_token("BOOK_QR"),status=CopyStatus.AVAILABLE);db.add(copy);copies.append(copy)
    db.flush();audit(db,"BOOK_CREATED","book",book.id,admin=admin,details={"initial_copy_count":payload.initial_copy_count})
    if copies:audit(db,"BOOK_COPIES_ADDED","book",book.id,admin=admin,details={"copy_ids":[copy.id for copy in copies]})
    db.commit();db.refresh(book);return book_dict(db,book)
@router.get("/{book_id}")
def get_book(book_id:int,db:Session=Depends(get_db)):
    book=db.scalar(select(Book).options(joinedload(Book.category)).where(Book.id==book_id))
    if not book:raise HTTPException(404,"Book not found.")
    data=book_dict(db,book);data["similar_books"]=[item for item in search_books(db,category=book.category.name,limit=6)[0] if item["id"]!=book.id][:5];return data
@router.put("/{book_id}")
def update_book(book_id:int,payload:BookUpdate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    book=db.get(Book,book_id)
    if not book:raise HTTPException(404,"Book not found.")
    was_archived=book.is_archived
    data=payload.model_dump(exclude_unset=True,exclude={"category","category_id","cover_image"})
    for k,v in data.items():setattr(book,k,v)
    if payload.category_id is not None or payload.category is not None:book.category_id=get_or_create_category(db,payload.category_id,payload.category).id
    if was_archived and book.is_archived is False:
        for copy in book.copies:
            if copy.status==CopyStatus.ARCHIVED:copy.status=CopyStatus.AVAILABLE
    audit(db,"BOOK_UPDATED","book",book.id,admin=admin,details={"fields":list(payload.model_fields_set)});db.commit();return book_dict(db,book)
@router.post("/{book_id}/archive")
def archive_book(book_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    book=db.get(Book,book_id)
    if not book:raise HTTPException(404,"Book not found.")
    book.is_archived=True
    for copy in book.copies:
        if copy.status==CopyStatus.AVAILABLE:copy.status=CopyStatus.ARCHIVED
    audit(db,"BOOK_ARCHIVED","book",book.id,admin=admin);db.commit();return book_dict(db,book)
@router.post("/{book_id}/copies",status_code=201)
def add_copies(book_id:int,payload:CopiesCreate,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    book=db.get(Book,book_id)
    if not book:raise HTTPException(404,"Book not found.")
    if book.is_archived:raise HTTPException(409,"Restore the catalog title before adding physical copies.")
    numbers=payload.accession_numbers or []
    if numbers and len(numbers)!=payload.quantity:raise HTTPException(422,"accession_numbers length must match quantity.")
    existing=db.scalar(select(func.count(BookCopy.id)).where(BookCopy.book_id==book_id)) or 0;created=[]
    for i in range(payload.quantity):
        accession=numbers[i] if numbers else f"BK-{book_id:05d}-C{existing+i+1:03d}";copy=BookCopy(book_id=book_id,accession_number=accession,qr_token=make_qr_token("BOOK_QR"),status=CopyStatus.AVAILABLE);db.add(copy);created.append(copy)
    db.flush();audit(db,"BOOK_COPIES_ADDED","book",book.id,admin=admin,details={"copy_ids":[c.id for c in created]});db.commit();return [{"id":c.id,"book_copy_id":c.id,"accession_number":c.accession_number,"status":c.status} for c in created]
@router.get("/{book_id}/copies")
def list_copies(book_id:int,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    return [{"id":c.id,"book_copy_id":c.id,"accession_number":c.accession_number,"status":c.status} for c in db.scalars(select(BookCopy).where(BookCopy.book_id==book_id))]

@router.post("/{book_id}/copies/qr-sheet",status_code=201)
def create_copy_qr_sheet(book_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    book=db.get(Book,book_id)
    if not book:raise HTTPException(404,"Book not found.")
    copies=list(db.scalars(select(BookCopy).where(BookCopy.book_id==book_id).order_by(BookCopy.accession_number)))
    if not copies:raise HTTPException(409,"Add at least one physical copy before generating a QR sheet.")
    path=generate_book_qr_sheet(book,copies);job=ReportJob(admin_id=admin.id,report_type="book_qr_sheet",format="pdf",file_path=str(path));db.add(job);db.flush();audit(db,"BOOK_QR_SHEET_EXPORTED","book",book.id,admin=admin,details={"copy_count":len(copies),"report_job_id":job.id});db.commit();ticket=create_report_download_grant(job.id);return {"job_id":job.id,"copy_count":len(copies),"download_url":f"/api/v1/reports/public-download/{ticket}"}

@router.post("/{book_id}/cover")
async def upload_cover(book_id:int,file:UploadFile=File(...),admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    book=db.get(Book,book_id)
    if not book:raise HTTPException(404,"Book not found.")
    content=await file.read(settings.max_upload_bytes+1)
    book.cover_image=store_image(content,file.content_type,"covers",book.id,book.cover_image)
    audit(db,"BOOK_COVER_UPDATED","book",book.id,admin=admin);db.commit();return {"book_id":book.id,"cover_url":book.cover_image}
