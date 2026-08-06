from datetime import datetime,timedelta,timezone
from fastapi import APIRouter,Depends
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_admin
from backend.models.entities import AIFeedback,AIInteraction,Admin,Book,BookCopy,Borrowing,BorrowingStatus,Category,CopyStatus,RenewalHistory,Reservation,ReservationStatus,SearchHistory,User
router=APIRouter(prefix="/admin",tags=["Dashboard"])
@router.get("/dashboard")
def dashboard(_admin:Admin=Depends(get_current_admin),db:Session=Depends(get_db)):
    now=datetime.now(timezone.utc);today=now.replace(hour=0,minute=0,second=0,microsecond=0)
    overdue=db.scalar(select(func.count(Borrowing.id)).where(Borrowing.status.in_([BorrowingStatus.ACTIVE,BorrowingStatus.OVERDUE]),Borrowing.due_at<now)) or 0
    by_day=[]
    for i in range(6,-1,-1):
        start=today-timedelta(days=i);end=start+timedelta(days=1);by_day.append({"date":start.date().isoformat(),"count":db.scalar(select(func.count(Borrowing.id)).where(Borrowing.borrowed_at>=start,Borrowing.borrowed_at<end)) or 0})
    categories=[{"category":name,"count":count} for name,count in db.execute(select(Category.name,func.count(Borrowing.id)).select_from(Category).join(Book,Book.category_id==Category.id).join(BookCopy,BookCopy.book_id==Book.id).join(Borrowing,Borrowing.book_copy_id==BookCopy.id).group_by(Category.id).order_by(func.count(Borrowing.id).desc()).limit(8)).all()]
    popular=[{"title":title,"count":count} for title,count in db.execute(select(Book.title,func.count(Borrowing.id)).select_from(Book).join(BookCopy,BookCopy.book_id==Book.id).join(Borrowing,Borrowing.book_copy_id==BookCopy.id).group_by(Book.id).order_by(func.count(Borrowing.id).desc()).limit(8)).all()]
    unmet=[{"query":query,"searches":count} for query,count in db.execute(select(func.lower(SearchHistory.query),func.count(SearchHistory.id)).where(SearchHistory.results_count==0).group_by(func.lower(SearchHistory.query)).order_by(func.count(SearchHistory.id).desc()).limit(5)).all()]
    ai_total=db.scalar(select(func.count(AIInteraction.id))) or 0;ai_fallbacks=db.scalar(select(func.count(AIInteraction.id)).where(AIInteraction.fallback_used.is_(True))) or 0
    feedback_total=db.scalar(select(func.count(AIFeedback.id))) or 0;helpful=db.scalar(select(func.count(AIFeedback.id)).where(AIFeedback.helpful.is_(True))) or 0
    data={"total_books":db.scalar(select(func.count(Book.id)).where(Book.is_archived.is_(False))) or 0,"total_copies":db.scalar(select(func.count(BookCopy.id)).where(BookCopy.status!=CopyStatus.ARCHIVED)) or 0,"available_books":db.scalar(select(func.count(BookCopy.id)).where(BookCopy.status==CopyStatus.AVAILABLE)) or 0,"available_copies":db.scalar(select(func.count(BookCopy.id)).where(BookCopy.status==CopyStatus.AVAILABLE)) or 0,"borrowed_books":db.scalar(select(func.count(BookCopy.id)).where(BookCopy.status==CopyStatus.BORROWED)) or 0,"borrowed_copies":db.scalar(select(func.count(BookCopy.id)).where(BookCopy.status==CopyStatus.BORROWED)) or 0,"overdue_books":overdue,"overdue_borrowings":overdue,"registered_users":db.scalar(select(func.count(User.id))) or 0,"transactions_today":db.scalar(select(func.count(Borrowing.id)).where(Borrowing.borrowed_at>=today)) or 0,"renewals_today":db.scalar(select(func.count(RenewalHistory.id)).where(RenewalHistory.renewed_at>=today)) or 0,"reservations":db.scalar(select(func.count(Reservation.id)).where(Reservation.status.in_([ReservationStatus.ACTIVE,ReservationStatus.READY]))) or 0,"active_reservations":db.scalar(select(func.count(Reservation.id)).where(Reservation.status.in_([ReservationStatus.ACTIVE,ReservationStatus.READY]))) or 0,"borrowings_by_day":by_day,"popular_categories":categories,"most_borrowed_books":popular,"unmet_searches":unmet,"ai_fallback_rate":round(ai_fallbacks/ai_total*100,1) if ai_total else 0,"ai_helpful_rate":round(helpful/feedback_total*100,1) if feedback_total else None}
    return data
