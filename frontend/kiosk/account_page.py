"""Private kiosk account summary, borrowing history, and reservations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

import flet as ft

from components.alert import Alert
from components.empty_state import EmptyState
from components.loading_view import InlineLoading
from components.page_shell import KioskView
from components.qr_scanner_view import QRScannerView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.borrowing_service import borrowing_service
from services.notification_service import notification_service
from services.qr_service import qr_service
from services.reservation_service import reservation_service
from utils.formatting import format_date


def _loan_card(item: dict, on_renew: Callable | None = None) -> ft.Container:
    status = str(item.get("status", "unknown")).lower()
    status_color = Colors.ERROR if status == "overdue" else Colors.SUCCESS if status == "returned" else Colors.PRIMARY
    due_note = ""
    raw_due = item.get("due_at")
    renewal_count = int(item.get("renewal_count", 0))
    max_renewals = int(item.get("max_renewals", 0))
    if raw_due and status in {"active", "overdue"}:
        try:
            due = datetime.fromisoformat(str(raw_due).replace("Z", "+00:00"))
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            days = (due.date() - datetime.now(timezone.utc).date()).days
            due_note = "Overdue" if days < 0 else "Due today" if days == 0 else f"Due in {days} day{'s' if days != 1 else ''}"
            if days <= 1:
                status_color = Colors.ERROR if days < 0 else Colors.WARNING
        except ValueError:
            pass
    return ft.Container(
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.MD,
        padding=Spacing.MD,
        content=ft.Row(
            controls=[
                ft.Container(width=42, height=54, border_radius=Radius.SM, bgcolor="#E8EDF7", alignment=ft.alignment.center, content=ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=Colors.PRIMARY)),
                ft.Column(expand=True, tight=True, spacing=2, controls=[ft.Text(str(item.get("book_title", "Unknown book")), weight=ft.FontWeight.W_600), ft.Text(f"Borrowed {format_date(item.get('borrowed_at'))}  •  Due {format_date(item.get('due_at'))}", size=12, color=Colors.TEXT_SECONDARY)]),
                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.END, tight=True, spacing=2, controls=[ft.Text(status.title(), size=12, weight=ft.FontWeight.W_600, color=status_color), *([ft.Text(due_note, size=10, color=status_color)] if due_note else []), *([ft.Text(f"Renewed {renewal_count}/{max_renewals}",size=10,color=Colors.TEXT_SECONDARY)] if max_renewals else []), *([ft.TextButton("Renew",icon=ft.Icons.UPDATE_ROUNDED,on_click=lambda event:on_renew(event,item))] if on_renew and item.get("can_renew") else [])]),
            ]
        ),
    )


def _account_action(page: ft.Page, icon: str, label: str, description: str, route: str) -> ft.Container:
    return ft.Container(
        col={"sm":12,"md":6,"xl":3},
        content=ft.Container(
            height=108,
            bgcolor=Colors.SURFACE,
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD,
            padding=Spacing.MD,
            ink=True,
            on_click=lambda _e: page.go(route),
            content=ft.Row(controls=[ft.Container(width=42,height=42,border_radius=Radius.SM,bgcolor=Colors.INFO_BG,alignment=ft.alignment.center,content=ft.Icon(icon,color=Colors.PRIMARY,size=21)),ft.Column(expand=True,tight=True,spacing=3,controls=[ft.Text(label,weight=ft.FontWeight.W_600),ft.Text(description,size=11,color=Colors.TEXT_SECONDARY)]),ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED,color=Colors.TEXT_DISABLED)]),
        ),
    )


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    body = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.LG)

    def end(_event) -> None:
        state.clear_kiosk()
        page.go(Routes.HOME)

    def verify(token: str):
        result = qr_service.verify_user(token)
        if result.ok:
            state.kiosk_user = result.data
            body.controls = [InlineLoading("Loading your private library account…")]
            page.update()
        else:
            body.controls.insert(0, Alert(result.error_kind, result.message))
        refresh()
        page.update()
        return result

    def refresh() -> None:
        body.controls.clear()
        if not state.kiosk_user:
            body.controls.extend([ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,tight=True,spacing=5,controls=[ft.Text("Sign in to My Account",size=28,weight=ft.FontWeight.W_700),ft.Text("Use your library QR to securely view your books and account activity.",color=Colors.TEXT_SECONDARY,text_align=ft.TextAlign.CENTER)]),QRScannerView(page, "Scan your library QR", "Your QR is verified by the library server and starts a private kiosk session.", verify, "Library user QR token")])
            return
        user = state.kiosk_user
        user_id = int(user["id"])
        grant = user.get("verification_token")
        loans_result = borrowing_service.list(user_id=user_id, verification_token=grant, limit=100)
        reservations_result = reservation_service.list(user_id, grant)
        notifications_result = notification_service.list(user_id, grant)
        loans = loans_result.data.get("items", []) if loans_result.ok and isinstance(loans_result.data, dict) else (loans_result.data if loans_result.ok else [])
        reservations = reservations_result.data.get("items", []) if reservations_result.ok and isinstance(reservations_result.data, dict) else (reservations_result.data if reservations_result.ok else [])
        notifications = notifications_result.data if notifications_result.ok and isinstance(notifications_result.data, list) else []
        active = [item for item in loans if str(item.get("status", "")).lower() in {"active", "overdue"}]
        history = [item for item in loans if item not in active]

        def renew(_event, item: dict) -> None:
            response = borrowing_service.renew(int(item["id"]), user_id, str(grant))
            message = response.data.get("due_at") if response.ok and isinstance(response.data, dict) else response.message
            page.open(ft.SnackBar(content=ft.Text(f"Renewed successfully. New due date: {format_date(message)}" if response.ok else str(message)),bgcolor=Colors.SUCCESS if response.ok else Colors.ERROR))
            if response.ok:
                refresh()
            page.update()
        summary = ft.Container(
            bgcolor=Colors.SURFACE,
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD,
            padding=Spacing.LG,
            content=ft.ResponsiveRow(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(col={"sm":12,"md":6}, content=ft.Row(controls=[ft.Container(width=62,height=62,border_radius=99,clip_behavior=ft.ClipBehavior.ANTI_ALIAS,bgcolor=Colors.PRIMARY_MUTED,alignment=ft.alignment.center,content=ft.Image(src=user.get("photo_url"),fit=ft.ImageFit.COVER) if user.get("photo_url") else ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, size=58, color=Colors.PRIMARY)), ft.Column(tight=True, controls=[ft.Text(str(user.get("name", "Library user")), size=22, weight=ft.FontWeight.W_700), ft.Text(str(user.get("student_id", "")), color=Colors.TEXT_SECONDARY), ft.Text(f"{user.get('course', '')} • Year {user.get('year_level', '—')}", size=12, color=Colors.TEXT_SECONDARY)])])),
                    ft.Container(col={"sm":12,"md":6}, content=ft.Row(alignment=ft.MainAxisAlignment.END, wrap=True, controls=[ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text(str(len(active)), size=22, weight=ft.FontWeight.W_700), ft.Text("Borrowed", size=11, color=Colors.TEXT_SECONDARY)]), ft.VerticalDivider(width=24), ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text(str(len(reservations)), size=22, weight=ft.FontWeight.W_700), ft.Text("Reservations", size=11, color=Colors.TEXT_SECONDARY)]), ft.OutlinedButton("End session", icon=ft.Icons.LOGOUT_ROUNDED, on_click=end)])),
                ],
            ),
        )
        status_text=str(user.get("account_status") or user.get("status") or "unknown").title()
        status_color=Colors.SUCCESS if status_text.lower()=="active" else Colors.WARNING
        actions=ft.ResponsiveRow(spacing=Spacing.MD,run_spacing=Spacing.MD,controls=[_account_action(page,ft.Icons.SEARCH_ROUNDED,"Browse catalog","Search all library titles.",Routes.SEARCH),_account_action(page,ft.Icons.QR_CODE_SCANNER_ROUNDED,"Borrow a book","Start the QR borrowing flow.",Routes.BORROW_SCAN_USER),_account_action(page,ft.Icons.RECOMMEND_OUTLINED,"For you","View personalized recommendations.",Routes.RECOMMENDATIONS),_account_action(page,ft.Icons.BOOKMARK_BORDER_ROUNDED,"Reservations","View or cancel your reservations.",Routes.RESERVATIONS)])
        account_state=ft.Container(bgcolor=Colors.SUCCESS_BG if status_color==Colors.SUCCESS else Colors.WARNING_BG,border_radius=Radius.MD,padding=Spacing.MD,content=ft.Row(controls=[ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED,color=status_color),ft.Column(expand=True,tight=True,controls=[ft.Text(f"Account {status_text}",weight=ft.FontWeight.W_600,color=status_color),ft.Text("You can use the kiosk borrowing services." if bool(user.get("can_borrow")) else "Borrowing may be restricted by account status, overdue items, or borrowing limit.",size=12,color=status_color)])]))
        controls: list[ft.Control] = [ft.Text("Account overview",size=25,weight=ft.FontWeight.W_700),summary,account_state,ft.Text("Quick actions",size=19,weight=ft.FontWeight.W_600),actions]
        unread = [item for item in notifications if not item.get("is_read")]
        if unread:
            def mark_read(_event, item: dict) -> None:
                response = notification_service.mark_read(int(item["id"]), str(grant))
                if response.ok:
                    item["is_read"] = True
                    refresh()
                    page.update()
            controls.extend([
                ft.Text(f"Notifications ({len(unread)} new)", size=19, weight=ft.FontWeight.W_600),
                *[ft.Container(bgcolor=Colors.INFO_BG,border_radius=Radius.MD,padding=Spacing.MD,content=ft.Row(controls=[ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,color=Colors.PRIMARY),ft.Text(str(item.get("message","Library notification")),expand=True,size=12),ft.TextButton("Mark read",on_click=lambda event, current=item:mark_read(event,current))])) for item in unread[:3]],
            ])
        if not loans_result.ok:
            controls.append(Alert(loans_result.error_kind, loans_result.message, "Borrowing history unavailable"))
        controls.extend([ft.Text("Currently borrowed", size=19, weight=ft.FontWeight.W_600), *([_loan_card(item, renew) for item in active] or [EmptyState("No borrowed books", "Your active loans will appear here.", ft.Icons.MENU_BOOK_OUTLINED)])])
        controls.extend([ft.Text("My reservations", size=19, weight=ft.FontWeight.W_600), ft.Text(f"{len(reservations)} active reservation(s)", color=Colors.TEXT_SECONDARY), ft.OutlinedButton("Open reservations", icon=ft.Icons.BOOKMARK_BORDER_ROUNDED, on_click=lambda _e: page.go(Routes.RESERVATIONS))])
        if history:
            controls.extend([ft.Text("Recent history", size=19, weight=ft.FontWeight.W_600), *[_loan_card(item) for item in history[:5]]])
        body.controls.extend(controls)

    refresh()
    return KioskView(page, Routes.ACCOUNT, "My Account", [body], state.kiosk_user.get("name") if state.kiosk_user else None)
