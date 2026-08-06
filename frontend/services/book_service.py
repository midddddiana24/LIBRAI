"""
LIBRAI - Book service.

Wraps the /books and /search/books endpoints. This module is the
reference pattern every other service should follow:

  1. Try the real backend via `api_client`.
  2. If the backend is unreachable AND `settings.use_mock_fallback`
     is True, fall back to a clearly-labeled mock so frontend
     development/demoing can continue without Codex's backend running.
  3. Never invent business rules (availability, fines, etc.) --
     those numbers, when mocked, are just illustrative placeholders.

See docs/frontend_api_requirements.md for the exact contract this
service expects from the backend.
"""

from __future__ import annotations

from typing import Any, Optional

from core.config import settings
from services.api_client import ApiResult, api_client

_MOCK_BOOKS = [
    {
        "id": 1,
        "title": "Python Crash Course",
        "author": "Eric Matthes",
        "isbn": "9781593279288",
        "publisher": "No Starch Press",
        "publication_year": 2019,
        "category": "Computer Science",
        "description": "A hands-on, project-based introduction to programming with Python.",
        "keywords": ["python", "programming", "beginner"],
        "cover_url": None,
        "available_copies": 2,
        "total_copies": 3,
        "shelf_location": "CS-104",
    },
    {
        "id": 2,
        "title": "Computer Networking: A Top-Down Approach",
        "author": "James F. Kurose",
        "isbn": "9780133594140",
        "publisher": "Pearson",
        "publication_year": 2016,
        "category": "Networking",
        "description": "Foundational concepts of computer networks, explained top-down.",
        "keywords": ["networking", "internet", "protocols"],
        "cover_url": None,
        "available_copies": 0,
        "total_copies": 2,
        "shelf_location": "NET-021",
    },
    {
        "id": 3,
        "title": "Introduction to Cybersecurity",
        "author": "Michael E. Whitman",
        "isbn": "9781305501791",
        "publisher": "Cengage",
        "publication_year": 2021,
        "category": "Cybersecurity",
        "description": "A beginner-friendly overview of information security principles.",
        "keywords": ["cybersecurity", "security", "beginner"],
        "cover_url": None,
        "available_copies": 4,
        "total_copies": 4,
        "shelf_location": "SEC-010",
    },
]


class BookService:
    def list_categories(self) -> ApiResult:
        return api_client.get("/categories")

    def list_books(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        available_only: bool = False,
        publication_year: Optional[int] = None,
        sort: str = "title",
        offset: int = 0,
        limit: int = 24,
    ) -> ApiResult:
        params: dict[str, Any] = {}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if author:
            params["author"] = author
        if available_only:
            params["available_only"] = True
        if publication_year:
            params["publication_year"] = publication_year
        params["sort"] = sort
        params["offset"] = offset
        params["limit"] = limit

        result = api_client.get("/search/books", params=params)
        if result.ok:
            return result

        if settings.use_mock_fallback:
            return self._mock_list(query, category, author, available_only)

        return result

    def get_book(self, book_id: int) -> ApiResult:
        result = api_client.get(f"/books/{book_id}")
        if result.ok:
            return result

        if settings.use_mock_fallback:
            for book in _MOCK_BOOKS:
                if book["id"] == book_id:
                    return ApiResult.success(book, is_mock=True)
            return ApiResult.failure("empty", "Book not found.")

        return result

    # ------------------------------------------------------------------
    def _mock_list(
        self,
        query: Optional[str],
        category: Optional[str],
        author: Optional[str],
        available_only: bool,
    ) -> ApiResult:
        books = _MOCK_BOOKS
        if query:
            q = query.lower()
            books = [
                b
                for b in books
                if q in b["title"].lower()
                or q in b["author"].lower()
                or q in b["category"].lower()
                or any(q in k for k in b["keywords"])
            ]
        if category:
            books = [b for b in books if b["category"].lower() == category.lower()]
        if author:
            books = [b for b in books if author.lower() in b["author"].lower()]
        if available_only:
            books = [b for b in books if b["available_copies"] > 0]

        return ApiResult.success(books, is_mock=True)


book_service = BookService()
