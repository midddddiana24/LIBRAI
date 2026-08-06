from __future__ import annotations
import flet as ft
from components.alert import Alert
from components.page_shell import KioskView
from components.qr_scanner_view import QRScannerView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing, touch_button_style
from services.qr_service import qr_service
from services.return_service import return_service
from utils.formatting import format_date


def _scan(page):
    state = get_state(page)
    status=ft.Column()
    def verify(token):
        book=qr_service.verify_book(token)
        if not book.ok:status.controls=[Alert(book.error_kind,book.message)];page.update();return book
        active=return_service.identify(book.data["id"],book.data.get("verification_token"))
        if active.ok:state.scanned_book=book.data;state.active_borrowing=active.data;page.go(Routes.RETURN_CONFIRM)
        else:
            status.controls=[Alert(active.error_kind,"This copy has no active borrowing to return. Borrow the copy first, or scan the QR of a currently borrowed copy.",title="No active borrowing")]
            page.update()
        return active
    return KioskView(page,Routes.RETURN_SCAN_BOOK,"Return Book",[status,QRScannerView(page,"Scan Book QR","The server will identify the active borrowing for this copy.",verify,"Book-copy QR token")])


def _confirm(page):
    state = get_state(page)
    if not state.active_borrowing:return _scan(page)
    b=state.active_borrowing;status=ft.Column()
    def submit(_e):
        if confirm_button.disabled:return
        confirm_button.disabled=True;confirm_button.text="Processing…"
        status.controls=[ft.Row(controls=[ft.ProgressRing(width=22,height=22,stroke_width=3),ft.Text("Validating and processing return…")])];page.update()
        r=return_service.create(b["id"],state.scanned_book.get("verification_token") if state.scanned_book else None)
        if r.ok:state.last_transaction=r.data;page.go(Routes.RETURN_SUCCESS)
        else:confirm_button.disabled=False;confirm_button.text="Confirm Return";status.controls=[Alert(r.error_kind,r.message)];page.update()
    confirm_button=ft.FilledButton("Confirm Return",icon=ft.Icons.KEYBOARD_RETURN_ROUNDED,style=touch_button_style(bg_color=Colors.SUCCESS),on_click=submit)
    card=ft.Container(width=680,bgcolor=Colors.SURFACE,border=ft.border.all(1,Colors.BORDER),border_radius=Radius.LG,padding=Spacing.XL,content=ft.Column(controls=[ft.Text("Confirm Return",size=26,weight=ft.FontWeight.BOLD),ft.Text(b.get("book_title"),size=20),ft.Text(f"Borrower: {b.get('user_name')} ({b.get('student_id')})"),ft.Text(f"Due date: {format_date(b.get('due_at'))}"),ft.Text("Any overdue policy is determined by the backend.",size=12,color=Colors.TEXT_SECONDARY),ft.Row(alignment=ft.MainAxisAlignment.END,controls=[ft.OutlinedButton("Cancel",on_click=lambda e:(state.clear_kiosk(),page.go(Routes.HOME))),confirm_button]),status]))
    return KioskView(page,Routes.RETURN_CONFIRM,"Return Book",[ft.Container(alignment=ft.alignment.center,content=card)])


def _success(page):
    state = get_state(page)
    t=state.last_transaction or {}
    def finish(_e):state.clear_kiosk();page.go(Routes.HOME)
    on_time=t.get("return_status")=="on_time"
    card=ft.Container(width=680,bgcolor=Colors.SURFACE,border=ft.border.all(1,Colors.BORDER),border_radius=Radius.LG,padding=Spacing.XL,content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,controls=[ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,size=84,color=Colors.SUCCESS),ft.Text("Return Successful",size=30,weight=ft.FontWeight.BOLD),ft.Text(t.get("book_title","Book"),size=19),ft.Text("Returned on time" if on_time else "Returned overdue",color=Colors.SUCCESS if on_time else Colors.WARNING,weight=ft.FontWeight.BOLD),ft.Text(f"Returned: {format_date(t.get('returned_at'))}"),ft.Text(f"Transaction ID: {t.get('transaction_id',t.get('id','—'))}",size=12,color=Colors.TEXT_SECONDARY),ft.FilledButton("Back to Home",style=touch_button_style(bg_color=Colors.SUCCESS),on_click=finish)]))
    return KioskView(page,Routes.RETURN_SUCCESS,"Return Book",[ft.Container(alignment=ft.alignment.center,content=card)])


def build_view(route,page):return {Routes.RETURN_SCAN_BOOK:_scan,Routes.RETURN_CONFIRM:_confirm,Routes.RETURN_SUCCESS:_success}.get(route,_scan)(page)
