from __future__ import annotations
import os
from sqlalchemy import select
from backend.core.database import SessionLocal
from backend.core.security import hash_password,make_qr_token
from backend.models.entities import Admin,Book,BookCopy,Category,CopyStatus,SystemSetting,User
from backend.services.policy_service import DEFAULTS


def seed() -> None:
    password=os.getenv("LIBRAI_SEED_ADMIN_PASSWORD")
    if not password or len(password)<12:raise SystemExit("Set LIBRAI_SEED_ADMIN_PASSWORD to at least 12 characters.")
    with SessionLocal() as db:
        admin=db.scalar(select(Admin).where(Admin.username=="admin"))
        if not admin:db.add(Admin(username="admin",email="admin@librai.local",password_hash=hash_password(password),role="SUPER_ADMIN"))
        else:admin.password_hash=hash_password(password)
        for key,value in DEFAULTS.items():
            if not db.scalar(select(SystemSetting).where(SystemSetting.key==key)):db.add(SystemSetting(key=key,value=value))
        user=db.scalar(select(User).where(User.student_id=="DEMO-2026-001"))
        if not user:user=User(student_id="DEMO-2026-001",first_name="Demo",last_name="Student",course="BS Information Technology",year_level="3",email="demo.student@librai.local",qr_token=make_qr_token("USR_QR"),status="ACTIVE");db.add(user)
        category=db.scalar(select(Category).where(Category.name=="Computer Science"))
        if not category:category=Category(name="Computer Science",description="Computing and information technology");db.add(category);db.flush()
        book=db.scalar(select(Book).where(Book.isbn=="9781593279288"))
        if not book:
            book=Book(isbn="9781593279288",title="Python Crash Course",author="Eric Matthes",publisher="No Starch Press",publication_year=2019,category_id=category.id,description="A hands-on introduction to Python.",keywords=["python","programming","beginner"],subjects=["Software Development"],shelf_location="CS-104");db.add(book);db.flush()
            for i in range(1,4):db.add(BookCopy(book_id=book.id,accession_number=f"BK-{book.id:05d}-C{i:03d}",qr_token=make_qr_token("BOOK_QR"),status=CopyStatus.AVAILABLE))
        db.commit();print("Seed complete. Admin username: admin");print(f"Demo user QR token: {user.qr_token}");print(f"Demo book QR token: {book.copies[0].qr_token}")

if __name__=="__main__":seed()
