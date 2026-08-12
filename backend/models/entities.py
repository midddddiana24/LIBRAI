from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdminRole(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    LIBRARIAN = "LIBRARIAN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class CopyStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    RESERVED = "RESERVED"
    LOST = "LOST"
    DAMAGED = "DAMAGED"
    ARCHIVED = "ARCHIVED"


class BorrowingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    LOST = "LOST"


class ReservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    READY = "READY"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class FineStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    WAIVED = "WAIVED"


class EmailDeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Admin(TimestampMixin, Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default=AdminRole.LIBRARIAN)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    course: Mapped[str] = mapped_column(String(150))
    year_level: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    photo_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=UserStatus.ACTIVE, index=True)
    borrowings: Mapped[list["Borrowing"]] = relationship(back_populates="user")
    fines: Mapped[list["Fine"]] = relationship(back_populates="user")

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    books: Mapped[list["Book"]] = relationship(back_populates="category")


class Book(TimestampMixin, Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    isbn: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    author: Mapped[str] = mapped_column(String(250), index=True)
    publisher: Mapped[str | None] = mapped_column(String(250), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    subjects: Mapped[list[str]] = mapped_column(JSON, default=list)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    shelf_location: Mapped[str] = mapped_column(String(100))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    category: Mapped[Category] = relationship(back_populates="books")
    copies: Mapped[list["BookCopy"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class BookCopy(TimestampMixin, Base):
    __tablename__ = "book_copies"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    accession_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    qr_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default=CopyStatus.AVAILABLE, index=True)
    book: Mapped[Book] = relationship(back_populates="copies")
    borrowings: Mapped[list["Borrowing"]] = relationship(back_populates="book_copy")


class Borrowing(Base):
    __tablename__ = "borrowings"
    __table_args__ = (
        Index("ix_borrowing_active_copy", "book_copy_id", "status"),
        Index("ix_borrowing_user_status_due", "user_id", "status", "due_at"),
        Index("uq_borrowing_one_active_per_copy", "book_copy_id", unique=True, sqlite_where=text("status IN ('ACTIVE','OVERDUE')"), postgresql_where=text("status IN ('ACTIVE','OVERDUE')")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    book_copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id", ondelete="RESTRICT"), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=BorrowingStatus.ACTIVE, index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="KIOSK")
    kiosk_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    renewal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user: Mapped[User] = relationship(back_populates="borrowings")
    book_copy: Mapped[BookCopy] = relationship(back_populates="borrowings")
    renewals: Mapped[list["RenewalHistory"]] = relationship(back_populates="borrowing", cascade="all, delete-orphan")
    fines: Mapped[list["Fine"]] = relationship(back_populates="borrowing")


class Fine(TimestampMixin, Base):
    __tablename__ = "fines"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    borrowing_id: Mapped[int | None] = mapped_column(ForeignKey("borrowings.id", ondelete="SET NULL"), nullable=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(120), default="OVERDUE")
    status: Mapped[str] = mapped_column(String(30), default=FineStatus.UNPAID, index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    user: Mapped[User] = relationship(back_populates="fines")
    borrowing: Mapped[Borrowing | None] = relationship(back_populates="fines")


class RenewalHistory(Base):
    __tablename__ = "renewal_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    borrowing_id: Mapped[int] = mapped_column(ForeignKey("borrowings.id", ondelete="CASCADE"), index=True)
    renewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    previous_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    new_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_type: Mapped[str] = mapped_column(String(30), default="KIOSK")
    borrowing: Mapped[Borrowing] = relationship(back_populates="renewals")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        Index("ix_reservation_queue", "book_id", "status", "reserved_at"),
        Index("uq_reservation_one_active_per_user_book", "user_id", "book_id", unique=True, sqlite_where=text("status IN ('ACTIVE','READY')"), postgresql_where=text("status IN ('ACTIVE','READY')")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=ReservationStatus.ACTIVE, index=True)
    user: Mapped[User] = relationship()
    book: Mapped[Book] = relationship()


class SearchHistory(Base):
    __tablename__ = "search_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    search_type: Mapped[str] = mapped_column(String(50), default="traditional")
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AIInteraction(Base):
    __tablename__ = "ai_interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    question: Mapped[str] = mapped_column(String(1000))
    response_summary: Mapped[str] = mapped_column(Text)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    feedback: Mapped[list["AIFeedback"]] = relationship(back_populates="interaction", cascade="all, delete-orphan")


class AIFeedback(Base):
    __tablename__ = "ai_feedback"
    __table_args__ = (Index("uq_ai_feedback_user_interaction", "interaction_id", "user_id", unique=True),)
    id: Mapped[int] = mapped_column(primary_key=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("ai_interactions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    helpful: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    interaction: Mapped[AIInteraction] = relationship(back_populates="feedback")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notification_id: Mapped[int | None] = mapped_column(ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=EmailDeliveryStatus.PENDING, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ReportJob(Base):
    __tablename__ = "report_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="RESTRICT"))
    report_type: Mapped[str] = mapped_column(String(60))
    format: Mapped[str] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
