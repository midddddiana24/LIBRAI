from __future__ import annotations
from datetime import datetime, time, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.models.entities import Book, BookCopy, Borrowing, BorrowingStatus, Category, User


def report_data(db: Session, report_type: str, start_date=None, end_date=None) -> tuple[list[str],list[list]]:
    today=datetime.now(timezone.utc).date()
    if not start_date and report_type=="daily_borrowing":start_date=today
    if not start_date and report_type=="weekly_borrowing":start_date=today-timedelta(days=6)
    if not start_date and report_type=="monthly_borrowing":start_date=today-timedelta(days=29)
    if not end_date and report_type in {"daily_borrowing","weekly_borrowing","monthly_borrowing"}:end_date=today
    if report_type=="inventory":
        headers=["ISBN","Title","Author","Accession","Status","Shelf"]
        rows=[[b.isbn,b.title,b.author,c.accession_number,c.status,b.shelf_location] for b,c in db.execute(select(Book,BookCopy).join(BookCopy)).all()]
    elif report_type=="overdue":
        headers=["Transaction","Student","Book","Due date"]
        rows=[[x.id,x.user.student_id,x.book_copy.book.title,x.due_at.isoformat()] for x in db.scalars(select(Borrowing).where(Borrowing.status.in_([BorrowingStatus.ACTIVE,BorrowingStatus.OVERDUE]),Borrowing.due_at<datetime.now(timezone.utc))).all()]
    elif report_type in {"most_borrowed","popular_categories"}:
        if report_type=="most_borrowed":
            headers=["Book","Borrow count"];rows=[[title,count] for title,count in db.execute(select(Book.title,func.count(Borrowing.id)).select_from(Book).join(BookCopy,BookCopy.book_id==Book.id).join(Borrowing,Borrowing.book_copy_id==BookCopy.id).group_by(Book.id).order_by(func.count(Borrowing.id).desc())).all()]
        else:
            headers=["Category","Borrow count"];rows=[[name,count] for name,count in db.execute(select(Category.name,func.count(Borrowing.id)).select_from(Category).join(Book,Book.category_id==Category.id).join(BookCopy,BookCopy.book_id==Book.id).join(Borrowing,Borrowing.book_copy_id==BookCopy.id).group_by(Category.id).order_by(func.count(Borrowing.id).desc())).all()]
    elif report_type=="user_activity":
        headers=["Student","Name","Borrow count"];rows=[[u.student_id,u.display_name,count] for u,count in db.execute(select(User,func.count(Borrowing.id)).outerjoin(Borrowing).group_by(User.id)).all()]
    else:
        headers=["Transaction","Student","Book","Borrowed","Due","Returned","Status"]
        stmt=select(Borrowing)
        if start_date:stmt=stmt.where(Borrowing.borrowed_at>=datetime.combine(start_date,time.min,tzinfo=timezone.utc))
        if end_date:stmt=stmt.where(Borrowing.borrowed_at<=datetime.combine(end_date,time.max,tzinfo=timezone.utc))
        rows=[[x.id,x.user.student_id,x.book_copy.book.title,x.borrowed_at.isoformat(),x.due_at.isoformat(),x.returned_at.isoformat() if x.returned_at else "",x.status] for x in db.scalars(stmt).all()]
    return headers,rows
