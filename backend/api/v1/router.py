from fastapi import APIRouter
from backend.api.v1 import ai,audit_logs,auth,book_copies,books,borrowings,categories,dashboard,notifications,qr,reports,reservations,returns,search,settings,speech,users
api_router=APIRouter()
for router in [auth.router,users.router,categories.router,books.router,book_copies.router,qr.router,borrowings.router,returns.router,reservations.router,search.router,ai.router,speech.router,dashboard.router,reports.router,audit_logs.router,notifications.router,settings.router]:api_router.include_router(router)
