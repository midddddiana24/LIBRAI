from pathlib import Path
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import create_report_download_grant,get_current_admin,verify_report_download_grant
from backend.models.entities import Admin,ReportJob
from backend.reports.generator import generate_report
from backend.schemas.api import ReportExportRequest
from backend.services.audit_service import audit
from backend.services.report_service import report_data
router=APIRouter(prefix="/reports",tags=["Reports"])
@router.get("")
def preview(report_type:Literal["daily_borrowing","weekly_borrowing","monthly_borrowing","overdue","inventory","most_borrowed","popular_categories","user_activity"]="daily_borrowing",start_date:date|None=None,end_date:date|None=None,_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    if start_date and end_date and start_date>end_date:raise HTTPException(422,"Start date must be on or before end date.")
    headers,rows=report_data(db,report_type,start_date,end_date);return {"report_type":report_type,"headers":headers,"items":rows[:100],"total":len(rows)}
@router.post("/export",status_code=201)
def export(payload:ReportExportRequest,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    headers,rows=report_data(db,payload.report_type,payload.start_date,payload.end_date);path=generate_report(payload.report_type,payload.format,headers,rows);job=ReportJob(admin_id=admin.id,report_type=payload.report_type,format=payload.format,file_path=str(path));db.add(job);db.flush();audit(db,"REPORT_EXPORTED","report_job",job.id,admin=admin,details={"type":payload.report_type,"format":payload.format});db.commit();ticket=create_report_download_grant(job.id);return {"job_id":job.id,"status":"completed","download_url":f"/api/v1/reports/public-download/{ticket}"}
@router.get("/{job_id}/download")
def download(job_id:int,admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    job=db.get(ReportJob,job_id)
    if not job or not job.file_path or not Path(job.file_path).is_file():raise HTTPException(404,"Report file not found.")
    return FileResponse(job.file_path,filename=Path(job.file_path).name)

@router.get("/public-download/{ticket}")
def public_download(ticket:str,db:Session=Depends(get_db)):
    job_id=verify_report_download_grant(ticket);job=db.get(ReportJob,job_id)
    if not job or not job.file_path or not Path(job.file_path).is_file():raise HTTPException(404,"Report file not found.")
    return FileResponse(job.file_path,filename=Path(job.file_path).name,headers={"Cache-Control":"no-store"})
