from fastapi import APIRouter
from backend.api.v1 import registrations
from backend.api.v1 import ai,audit_logs,auth,book_copies,books,borrowings,categories,dashboard,fines,notifications,qr,reports,reservations,returns,search,settings,speech,users
api_router=APIRouter()
api_router.include_router(registrations.router)
for router in [auth.router,users.router,categories.router,books.router,book_copies.router,qr.router,borrowings.router,returns.router,reservations.router,search.router,ai.router,speech.router,dashboard.router,reports.router,audit_logs.router,notifications.router,fines.router,settings.router]:api_router.include_router(router)
