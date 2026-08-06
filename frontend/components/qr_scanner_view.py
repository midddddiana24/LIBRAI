"""Laptop-camera QR scanner with a secure manual-entry fallback."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Callable
import uuid

import flet as ft

from core.config import settings
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.qr_service import qr_service

try:  # Optional until the frontend requirements are installed again.
    import cv2
except ImportError:  # pragma: no cover - environment-dependent adapter
    cv2 = None


def QRScannerView(page: ft.Page, title: str, subtitle: str, on_scan: Callable[[str], object], token_hint: str) -> ft.Container:
    """Render and control a local laptop webcam QR scanner.

    In Flet web mode this opens the camera attached to the computer running
    the Python frontend process. It is therefore intended for a kiosk laptop,
    not for a remotely hosted frontend server.
    """
    initial_route = page.route
    app_state = get_state(page)
    camera_state = {"running": False}
    verification_state = {"running": False}
    preview = ft.Image(width=520, height=292, fit=ft.ImageFit.COVER, gapless_playback=True, visible=False)
    placeholder = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.SM, controls=[ft.Icon(ft.Icons.VIDEOCAM_OUTLINED, size=56, color="#C7D7EA"), ft.Text("Camera preview", color="#DCE7F2", weight=ft.FontWeight.W_600), ft.Text("Place the QR code inside the frame", size=12, color="#8FA8C1")])
    status = ft.Text("Ready to scan", color=Colors.TEXT_SECONDARY, weight=ft.FontWeight.W_600)
    phase_nodes = [ft.Container(border_radius=Radius.PILL, padding=ft.padding.symmetric(horizontal=10, vertical=6)) for _ in range(3)]

    def set_phase(active: int) -> None:
        labels = ["Position QR", "Detect", "Verify"]
        for index, node in enumerate(phase_nodes):
            complete = index < active
            selected = index == active
            node.bgcolor = Colors.SUCCESS_BG if complete else Colors.INFO_BG if selected else Colors.BACKGROUND
            node.content = ft.Row(tight=True, spacing=5, controls=[ft.Icon(ft.Icons.CHECK_ROUNDED if complete else ft.Icons.CIRCLE_OUTLINED, size=14, color=Colors.SUCCESS if complete else Colors.PRIMARY if selected else Colors.TEXT_DISABLED), ft.Text(labels[index], size=10, weight=ft.FontWeight.W_600, color=Colors.SUCCESS if complete else Colors.PRIMARY if selected else Colors.TEXT_DISABLED)])

    set_phase(0)
    phases = ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=6, controls=phase_nodes)
    camera_button = ft.FilledButton("Start laptop camera", icon=ft.Icons.VIDEOCAM_ROUNDED)
    stop_button = ft.OutlinedButton("Stop camera", icon=ft.Icons.STOP_CIRCLE_OUTLINED, visible=False)
    token = ft.TextField(label="Secure QR token", hint_text=token_hint, password=True, can_reveal_password=True, border_radius=Radius.SM)
    manual = ft.Column(visible=cv2 is None, spacing=Spacing.MD, controls=[ft.Divider(color=Colors.BORDER), ft.Text("Manual entry", weight=ft.FontWeight.W_600), ft.Text("Use this only for development or when the camera is unavailable.", size=12, color=Colors.TEXT_SECONDARY), token])
    manual_toggle = ft.TextButton("Use manual entry instead", icon=ft.Icons.KEYBOARD_ROUNDED)

    def submit(_event) -> None:
        app_state.touch()
        value = str(token.value or "").strip()
        if value and not verification_state["running"]:
            verification_state["running"] = True
            set_phase(2)
            status.value = "QR entered — verifying with library server…"
            status.color = Colors.PRIMARY
            page.update()
            result = on_scan(value)
            verification_state["running"] = False
            if result is not None and getattr(result, "ok", True) is False:
                status.value = str(getattr(result, "message", "QR verification failed."))
                status.color = Colors.ERROR
                set_phase(0)
                camera_button.disabled = False
                manual.visible = True
                page.update()

    manual.controls.append(ft.FilledButton("Verify QR", icon=ft.Icons.CHECK_ROUNDED, on_click=submit))

    def toggle_manual(_event) -> None:
        manual.visible = not manual.visible
        manual_toggle.text = "Hide manual entry" if manual.visible else "Use manual entry instead"
        page.update()

    manual_toggle.on_click = toggle_manual

    def stop_camera(_event=None) -> None:
        camera_state["running"] = False
        camera_button.disabled = False
        stop_button.visible = False
        status.value = "Camera stopped"
        status.color = Colors.TEXT_SECONDARY
        set_phase(0)
        page.update()

    def deliver_decoded(value: str) -> None:
        """Run API verification in Flet's normal handler executor.

        The camera loop runs on the page asyncio loop. Performing the blocking
        HTTP verification and route change directly inside that loop can leave
        the UI at "QR detected" without dispatching navigation.
        """
        try:
            app_state.touch()
            verification_state["running"] = True
            result = on_scan(value)
            verification_state["running"] = False
            if result is not None and getattr(result, "ok", True) is False:
                status.value = str(getattr(result, "message", "QR verification failed."))
                status.color = Colors.ERROR
                set_phase(0)
                camera_button.disabled = False
                manual.visible = True
                page.update()
        except Exception:
            verification_state["running"] = False
            status.value = "QR was detected, but verification could not finish. Please try again."
            status.color = Colors.ERROR
            camera_button.disabled = False
            manual.visible = True
            page.update()

    photo_status = ft.Text("On a tablet, choose Camera when prompted.", size=11, color=Colors.TEXT_SECONDARY)
    photo_progress = ft.ProgressBar(visible=False, color=Colors.PRIMARY)
    photo_button = ft.OutlinedButton("Take or choose QR photo", icon=ft.Icons.ADD_A_PHOTO_OUTLINED)
    photo_state: dict[str, Path | None] = {"temporary": None}

    def decode_photo(path: Path) -> None:
        app_state.touch()
        photo_button.disabled = True
        photo_progress.visible = True
        photo_progress.value = None
        photo_status.value = "Reading QR code from photo…"
        photo_status.color = Colors.PRIMARY
        page.update()
        decoded = qr_service.decode_image(str(path))
        photo_progress.visible = False
        photo_button.disabled = False
        temporary = photo_state.get("temporary")
        if temporary and temporary.is_file():
            root = settings.frontend_upload_directory.resolve()
            candidate = temporary.resolve()
            if root in candidate.parents:
                candidate.unlink()
            photo_state["temporary"] = None
        if not decoded.ok:
            photo_status.value = decoded.message
            photo_status.color = Colors.ERROR
            set_phase(0)
            page.update()
            return
        value = str((decoded.data or {}).get("token") or "").strip()
        if not value:
            photo_status.value = "The server could not read a QR token from this photo."
            photo_status.color = Colors.ERROR
            page.update()
            return
        photo_status.value = "QR detected — verifying with library server…"
        photo_status.color = Colors.SUCCESS
        page.update()
        deliver_decoded(value)

    def photo_uploaded(event) -> None:
        if event.error:
            photo_progress.visible = False
            photo_button.disabled = False
            photo_status.value = f"Photo upload failed: {event.error}"
            photo_status.color = Colors.ERROR
        elif event.progress is not None:
            photo_progress.value = event.progress
            if event.progress >= 1:
                temporary = photo_state.get("temporary")
                if temporary and temporary.is_file():
                    decode_photo(temporary)
                else:
                    photo_progress.visible = False
                    photo_button.disabled = False
                    photo_status.value = "Upload finished, but the photo could not be opened."
                    photo_status.color = Colors.ERROR
        page.update()

    def photo_picked(event) -> None:
        if not event.files:
            return
        selected = event.files[0]
        if selected.size and selected.size > 5*1024*1024:
            photo_status.value = "QR photo is larger than 5 MB. Choose a smaller image."
            photo_status.color = Colors.ERROR
            page.update()
            return
        local = Path(selected.path) if selected.path else None
        if local and local.is_file():
            decode_photo(local)
            return
        suffix = Path(selected.name).suffix.lower()
        staged_name = f"qr-photo-{uuid.uuid4().hex}{suffix}"
        settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
        temporary = settings.frontend_upload_directory / staged_name
        photo_state["temporary"] = temporary
        photo_button.disabled = True
        photo_progress.visible = True
        photo_status.value = f"Uploading {selected.name}…"
        photo_status.color = Colors.PRIMARY
        page.update()
        photo_picker.upload([ft.FilePickerUploadFile(name=selected.name,upload_url=page.get_upload_url(staged_name,600))])

    photo_picker = ft.FilePicker(on_result=photo_picked,on_upload=photo_uploaded)
    page.overlay.append(photo_picker)
    photo_button.on_click = lambda _event: photo_picker.pick_files(
        dialog_title="Take or choose a QR photo",
        file_type=ft.FilePickerFileType.CUSTOM,
        allowed_extensions=["jpg","jpeg","png","webp"],
        allow_multiple=False,
    )

    async def camera_loop() -> None:
        if cv2 is None:
            status.value = "Camera support is not installed. Reinstall frontend requirements and restart Flet."
            status.color = Colors.WARNING
            manual.visible = True
            camera_button.disabled = True
            page.update()
            return
        capture = await asyncio.to_thread(cv2.VideoCapture, settings.camera_index)
        if not capture.isOpened():
            status.value = "Laptop camera unavailable. Close other camera apps or use manual entry."
            status.color = Colors.ERROR
            camera_button.disabled = False
            stop_button.visible = False
            manual.visible = True
            capture.release()
            page.update()
            return
        detector = cv2.QRCodeDetector()
        decoded = ""
        try:
            while camera_state["running"] and page.route == initial_route:
                ok, frame = await asyncio.to_thread(capture.read)
                if not ok:
                    status.value = "Camera frame could not be read."
                    status.color = Colors.ERROR
                    break
                decoded, points, _straight = detector.detectAndDecode(frame)
                if points is not None:
                    points = points.astype(int).reshape(-1, 2)
                    for index in range(len(points)):
                        cv2.line(frame, tuple(points[index]), tuple(points[(index + 1) % len(points)]), (34, 197, 94), 3)
                frame = cv2.resize(frame, (520, 292))
                encoded_ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
                if encoded_ok:
                    preview.src_base64 = base64.b64encode(buffer).decode("ascii")
                    preview.visible = True
                    placeholder.visible = False
                    page.update()
                if decoded:
                    set_phase(2)
                    status.value = "QR detected — verifying with library server…"
                    status.color = Colors.SUCCESS
                    camera_state["running"] = False
                    page.update()
                    break
                await asyncio.sleep(0.08)
        finally:
            capture.release()
            camera_button.disabled = False
            stop_button.visible = False
        if decoded and page.route == initial_route:
            page.run_thread(deliver_decoded, decoded.strip())

    def start_camera(_event) -> None:
        app_state.touch()
        if camera_state["running"]:
            return
        camera_state["running"] = True
        camera_button.disabled = True
        stop_button.visible = True
        status.value = "Starting camera…"
        status.color = Colors.PRIMARY
        set_phase(1)
        page.update()
        page.run_task(camera_loop)

    camera_button.on_click = start_camera
    stop_button.on_click = stop_camera
    camera_panel = ft.Container(
        width=540,
        height=312,
        bgcolor="#102A43",
        border_radius=Radius.MD,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.alignment.center,
        content=ft.Stack(
            controls=[
                preview,
                ft.Container(alignment=ft.alignment.center, content=placeholder),
                ft.Container(left=34, top=28, width=472, height=256, border=ft.border.all(2, ft.Colors.with_opacity(0.8, Colors.ON_PRIMARY)), border_radius=Radius.MD),
            ]
        ),
    )
    card = ft.Container(
        width=650,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.MD,
        padding=Spacing.XL,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.MD,
            controls=[
                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=5, controls=[ft.Text(title, size=25, weight=ft.FontWeight.W_700), ft.Text(subtitle, size=13, color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)]),
                phases,
                camera_panel,
                status,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[camera_button, stop_button]),
                ft.Container(
                    width=520,
                    bgcolor=Colors.INFO_BG,
                    border=ft.border.all(1, Colors.BORDER),
                    border_radius=Radius.SM,
                    padding=Spacing.MD,
                    content=ft.Column(
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=Spacing.SM,
                        controls=[
                            ft.Text("Use this tablet or phone", weight=ft.FontWeight.W_700, color=Colors.TEXT_PRIMARY),
                            ft.Text("Take a clear photo of one QR code, or choose an existing QR image.", size=12, color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                            photo_button,
                            photo_progress,
                            photo_status,
                        ],
                    ),
                ),
                manual_toggle,
                ft.Container(width=520, content=manual),
                ft.Text("The decoded token is validated by the LIBRAI backend. Personal details are not stored in the QR image.", size=11, color=Colors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )
    return ft.Container(alignment=ft.alignment.top_center, content=card)
