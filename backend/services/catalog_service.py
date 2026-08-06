from __future__ import annotations
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import Session, joinedload
from backend.models.entities import Book, BookCopy, Category, CopyStatus, SearchHistory
from backend.services.serialization import book_dict


def search_books(db: Session, q=None, category=None, author=None, available_only=False, publication_year=None, offset=0, limit=50, user_id=None, search_type="traditional", sort="title") -> tuple[list[dict], int]:
    stmt = select(Book).options(joinedload(Book.category)).where(Book.is_archived.is_(False))
    if q:
        term = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Book.title).like(term), func.lower(Book.author).like(term), func.lower(Book.isbn).like(term), func.lower(Book.description).like(term), func.lower(cast(Book.keywords, String)).like(term), func.lower(cast(Book.subjects, String)).like(term)))
    if category: stmt = stmt.join(Book.category).where(func.lower(Category.name) == category.lower())
    if author: stmt = stmt.where(func.lower(Book.author).like(f"%{author.lower()}%"))
    if publication_year: stmt = stmt.where(Book.publication_year == publication_year)
    if available_only: stmt = stmt.where(Book.copies.any(BookCopy.status == CopyStatus.AVAILABLE))
    count = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    if sort == "newest":
        order = (Book.created_at.desc(), Book.title)
    elif sort == "availability":
        available_count = select(func.count(BookCopy.id)).where(BookCopy.book_id == Book.id, BookCopy.status == CopyStatus.AVAILABLE).correlate(Book).scalar_subquery()
        order = (available_count.desc(), Book.title)
    else:
        order = (Book.title,)
    books = db.scalars(stmt.order_by(*order).offset(offset).limit(min(limit, 100))).unique().all()
    items = [book_dict(db, book) for book in books]
    if q:
        db.add(SearchHistory(user_id=user_id, query=q[:500], search_type=search_type, results_count=count)); db.commit()
    return items, count


def get_or_create_category(db: Session, category_id: int | None, name: str | None) -> Category:
    category = db.get(Category, category_id) if category_id else None
    if not category and name:
        category = db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))
        if not category: category = Category(name=name.strip()); db.add(category); db.flush()
    if not category: raise ValueError("A valid category_id or category name is required.")
    return category
