from __future__ import annotations

from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class QRVerifyRequest(BaseModel):
    token: str | None = Field(default=None, min_length=12, max_length=300)
    qr_token: str | None = Field(default=None, min_length=12, max_length=300)
    @property
    def resolved_token(self): return self.token or self.qr_token

    @field_validator("qr_token")
    @classmethod
    def at_least_one(cls, value, info):
        if not value and not info.data.get("token"): raise ValueError("token or qr_token is required")
        return value


class UserCreate(BaseModel):
    student_id: str = Field(min_length=2, max_length=80)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    course: str = Field(min_length=1, max_length=150)
    year_level: str = Field(min_length=1, max_length=30)
    email: EmailStr | None = None
    contact_number: str | None = Field(default=None, max_length=40)
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED"] = "ACTIVE"


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    course: str | None = Field(default=None, min_length=1, max_length=150)
    year_level: str | None = None
    email: EmailStr | None = None
    contact_number: str | None = None
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED"] | None = None


class BookCreate(BaseModel):
    isbn: str = Field(min_length=3, max_length=32)
    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=250)
    publisher: str | None = None
    publication_year: int | None = Field(default=None, ge=1000, le=2200)
    category_id: int | None = None
    category: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    cover_image: str | None = None
    shelf_location: str = Field(min_length=1, max_length=100)
    initial_copy_count: int = Field(default=0, ge=0, le=100)


class BookUpdate(BaseModel):
    isbn: str | None = None
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    publication_year: int | None = Field(default=None, ge=1000, le=2200)
    category_id: int | None = None
    category: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    subjects: list[str] | None = None
    cover_image: str | None = None
    shelf_location: str | None = None
    is_archived: bool | None = None


class CopiesCreate(BaseModel):
    quantity: int = Field(default=1, ge=1, le=100)
    accession_numbers: list[str] | None = None


class CopyUpdate(BaseModel):
    status: Literal["AVAILABLE", "BORROWED", "RESERVED", "LOST", "DAMAGED", "ARCHIVED"]


class BorrowCreate(BaseModel):
    user_id: int
    book_copy_id: int
    kiosk_id: str | None = Field(default=None, max_length=100)
    user_verification_token: str | None = None
    book_verification_token: str | None = None


class ReturnCreate(BaseModel):
    borrowing_id: int
    book_verification_token: str | None = None


class RenewRequest(BaseModel):
    user_id: int
    user_verification_token: str | None = None


class NotificationReadRequest(BaseModel):
    verification_token: str | None = None


class FinePaymentRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ReservationCreate(BaseModel):
    user_id: int
    book_id: int
    user_verification_token: str | None = None


class AIRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    user_id: int | None = None
    user_verification_token: str | None = None


class RecommendRequest(BaseModel):
    user_id: int | None = None
    kind: Literal["personalized", "recommended", "popular", "new", "available"] = "personalized"
    user_verification_token: str | None = None


class AIFeedbackRequest(BaseModel):
    interaction_id: int
    user_id: int | None = None
    user_verification_token: str | None = None
    helpful: bool
    reason: str | None = Field(default=None, max_length=500)


class ReportExportRequest(BaseModel):
    report_type: Literal["daily_borrowing", "weekly_borrowing", "monthly_borrowing", "overdue", "inventory", "most_borrowed", "popular_categories", "user_activity", "unpaid_fines"]
    start_date: date | None = None
    end_date: date | None = None
    format: Literal["pdf", "csv", "xlsx"] = "pdf"
