from __future__ import annotations
import flet as ft
from components.alert import Alert
from components.page_shell import KioskView
from components.qr_scanner_view import QRScannerView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing, touch_button_style
from services.borrowing_service import borrowing_service
from services.api_client import ApiResult
from services.qr_service import qr_service
from utils.formatting import format_date


def _steps(active: int) -> ft.Row:
    labels=["User QR", "Verify user", "Book QR", "Confirm", "Complete"]
    return ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True, controls=[ft.Container(padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=99, bgcolor=Colors.PRIMARY if i<=active else "#E5E7EB", content=ft.Text(f"{i+1}. {x}", color=Colors.ON_PRIMARY if i<=active else Colors.TEXT_SECONDARY, size=12)) for i,x in enumerate(labels)])


def _scan_user(page):
    state = get_state(page)
    status=ft.Column()
    def scan(token):
        r=qr_service.verify_user(token)
        if r.ok: state.kiosk_user=r.data; page.go(Routes.BORROW_USER_VERIFIED)
        else: status.controls=[Alert(r.error_kind,r.message)]; page.update()
        return r
    return KioskView(page, Routes.BORROW_SCAN_USER, "Borrow Book", [_steps(0), status, QRScannerView(page, "Scan Your Library QR", "Your QR is verified securely by the library server.", scan, "Library user QR token")])


def _verified(page):
    state = get_state(page)
    if not state.kiosk_user: return _scan_user(page)
    u=state.kiosk_user
    rows=[("Name",u.get("name")),("Student ID",u.get("student_id")),("Course",u.get("course")),("Account status",u.get("account_status","unknown").title()),("Current borrowed",f"{u.get('current_borrowed_count',0)} of {u.get('borrowing_limit','—')}"),("Overdue status","Has overdue items" if u.get("has_overdue") else "Clear")]
    can_borrow=bool(u.get("can_borrow",True))
    restriction=[] if can_borrow else [Alert("validation_error","This account cannot borrow right now. Check the account status, borrowing limit, and overdue items.",title="Borrowing restricted")]
    card=ft.Container(width=680,bgcolor=Colors.SURFACE,border_radius=Radius.LG,padding=Spacing.XL,content=ft.Column(controls=[ft.Text("User Verified",size=26,weight=ft.FontWeight.BOLD,color=Colors.SUCCESS),*[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,controls=[ft.Text(a,color=Colors.TEXT_SECONDARY),ft.Text(str(b),weight=ft.FontWeight.W_600)]) for a,b in rows],*restriction,ft.Row(controls=[ft.OutlinedButton("Cancel",on_click=lambda e:(state.clear_kiosk(),page.go(Routes.HOME))),ft.FilledButton("Continue",icon=ft.Icons.ARROW_FORWARD_ROUNDED,style=touch_button_style(),disabled=not can_borrow,on_click=lambda e:page.go(Routes.BORROW_SCAN_BOOK))])]))
    return KioskView(page,Routes.BORROW_USER_VERIFIED,"Borrow Book",[_steps(1),ft.Container(alignment=ft.alignment.center,content=card)],u.get("name"))


def _scan_book(page):
    state = get_state(page)
    if not state.kiosk_user: return _scan_user(page)
    status=ft.Column()
    def scan(token):
        r=qr_service.verify_book(token)
        if r.ok and not bool(r.data.get("can_borrow",r.data.get("available",False))):
            r=ApiResult.failure("validation_error","This physical copy is not available for borrowing.",409)
        if r.ok: state.scanned_book=r.data; page.go(Routes.BORROW_CONFIRM)
        else: status.controls=[Alert(r.error_kind,r.message)];page.update()
        return r
    return KioskView(page,Routes.BORROW_SCAN_BOOK,"Borrow Book",[_steps(2),status,QRScannerView(page,"Scan Book QR","Scan the secure QR attached to the physical book copy.",scan,"Book-copy QR token")],state.kiosk_user.get("name"))


def _confirm(page):
    state = get_state(page)
    if not state.kiosk_user:return _scan_user(page)
    if not state.scanned_book:return _scan_book(page)
    b=state.scanned_book; status=ft.Column()
    def submit(_e):
        if confirm_button.disabled:return
        confirm_button.disabled=True;confirm_button.text="Processing…"
        status.controls=[ft.Row(controls=[ft.ProgressRing(width=22,height=22,stroke_width=3),ft.Text("Checking account, policy, availability, and processing transaction…")])];page.update()
        r=borrowing_service.create(state.kiosk_user["id"],b["id"],state.kiosk_user.get("verification_token"),b.get("verification_token"))
        if r.ok:state.last_transaction=r.data;page.go(Routes.BORROW_SUCCESS)
        else:confirm_button.disabled=False;confirm_button.text="Confirm Borrow";status.controls=[Alert(r.error_kind,r.message)];page.update()
    confirm_button=ft.FilledButton("Confirm Borrow",icon=ft.Icons.CHECK_ROUNDED,style=touch_button_style(),disabled=not bool(b.get("can_borrow",b.get("available",False))),on_click=submit)
    card=ft.Container(width=720,bgcolor=Colors.SURFACE,border=ft.border.all(1,Colors.BORDER),border_radius=Radius.LG,padding=Spacing.XL,content=ft.Row(wrap=True,controls=[ft.Container(width=160,height=210,bgcolor="#E8EDF7",border_radius=Radius.MD,alignment=ft.alignment.center,content=ft.Icon(ft.Icons.MENU_BOOK_ROUNDED,size=60,color=Colors.PRIMARY)),ft.Column(expand=True,controls=[ft.Text(b.get("title"),size=25,weight=ft.FontWeight.BOLD),ft.Text(b.get("author")),ft.Text(f"Category: {b.get('category','—')}"),ft.Text(f"Copy ID: {b.get('copy_id','—')}"),ft.Text(f"Shelf: {b.get('shelf_location','—')}"),ft.Text("Available" if b.get("available") else "Unavailable",color=Colors.SUCCESS if b.get("available") else Colors.ERROR),ft.Row(alignment=ft.MainAxisAlignment.END,controls=[ft.OutlinedButton("Cancel",on_click=lambda e:(state.clear_kiosk(),page.go(Routes.HOME))),confirm_button]),status])]))
    return KioskView(page,Routes.BORROW_CONFIRM,"Borrow Book",[_steps(3),ft.Container(alignment=ft.alignment.center,content=card)],state.kiosk_user.get("name"))


def _success(page):
    state = get_state(page)
    t=state.last_transaction or {}
    def another(_e):state.scanned_book=None;state.last_transaction=None;page.go(Routes.BORROW_SCAN_BOOK)
    def finish(_e):state.clear_kiosk();page.go(Routes.HOME)
    card=ft.Container(width=680,bgcolor=Colors.SURFACE,border=ft.border.all(1,Colors.BORDER),border_radius=Radius.LG,padding=Spacing.XL,content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,size=84,color=Colors.SUCCESS),ft.Text("Borrowing Successful",size=30,weight=ft.FontWeight.BOLD),ft.Text(t.get("book_title","Book"),size=19),ft.Text(f"Borrowed: {format_date(t.get('borrowed_at'))}"),ft.Text(f"Due date: {format_date(t.get('due_at'))}",weight=ft.FontWeight.BOLD,color=Colors.WARNING),ft.Text(f"Transaction ID: {t.get('transaction_id',t.get('id','—'))}",size=12,color=Colors.TEXT_SECONDARY),ft.Row(wrap=True,alignment=ft.MainAxisAlignment.CENTER,controls=[ft.OutlinedButton("Borrow Another Book",on_click=another),ft.FilledButton("Finish",on_click=finish)])]))
    return KioskView(page,Routes.BORROW_SUCCESS,"Borrow Book",[_steps(4),ft.Container(alignment=ft.alignment.center,content=card)])


def build_view(route,page):
    return {Routes.BORROW_SCAN_USER:_scan_user,Routes.BORROW_USER_VERIFIED:_verified,Routes.BORROW_SCAN_BOOK:_scan_book,Routes.BORROW_CONFIRM:_confirm,Routes.BORROW_SUCCESS:_success}.get(route,_scan_user)(page)
