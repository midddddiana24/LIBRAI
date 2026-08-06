from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.models.entities import Book, BookCopy, Borrowing, BorrowingStatus, CopyStatus, User
from backend.core.security import create_user_photo_grant


def book_dict(db: Session, book: Book) -> dict:
    total = db.scalar(select(func.count(BookCopy.id)).where(BookCopy.book_id == book.id, BookCopy.status != CopyStatus.ARCHIVED)) or 0
    available = db.scalar(select(func.count(BookCopy.id)).where(BookCopy.book_id == book.id, BookCopy.status == CopyStatus.AVAILABLE)) or 0
    return {"id": book.id, "isbn": book.isbn, "title": book.title, "author": book.author, "publisher": book.publisher, "publication_year": book.publication_year, "category": book.category.name if book.category else None, "category_id": book.category_id, "description": book.description, "keywords": book.keywords or [], "subjects": book.subjects or [], "cover_url": book.cover_image, "cover_image": book.cover_image, "shelf_location": book.shelf_location, "available_copies": available, "total_copies": total, "created_at": book.created_at, "is_archived": book.is_archived}


def user_safe_dict(db: Session, user: User, borrowing_limit: int) -> dict:
    active = db.scalar(select(func.count(Borrowing.id)).where(Borrowing.user_id == user.id, Borrowing.status.in_([BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE]))) or 0
    overdue = db.scalar(select(func.count(Borrowing.id)).where(Borrowing.user_id == user.id, Borrowing.status.in_([BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE]), Borrowing.due_at < datetime.now(timezone.utc))) or 0
    photo_url = f"/api/v1/users/photo/{create_user_photo_grant(user.id)}" if user.photo_image else None
    return {"id": user.id, "user_id": user.id, "name": user.display_name, "display_name": user.display_name, "student_id": user.student_id, "course": user.course, "year_level": user.year_level, "photo_url": photo_url, "status": user.status.lower(), "account_status": user.status.lower(), "current_borrowed_count": active, "active_borrowing_count": active, "borrowing_limit": borrowing_limit, "has_overdue": overdue > 0, "has_overdue_books": overdue > 0, "can_borrow": user.status == "ACTIVE" and active < borrowing_limit and overdue == 0}


def user_admin_dict(db: Session, user: User, borrowing_limit: int) -> dict:
    """Administrative user projection with editable contact fields.

    QR tokens, password/PIN hashes, and other authentication material are
    deliberately excluded.
    """
    data = user_safe_dict(db, user, borrowing_limit)
    data.update(
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "contact_number": user.contact_number,
        }
    )
    return data
