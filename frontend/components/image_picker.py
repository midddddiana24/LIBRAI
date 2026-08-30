"""Reusable Flet image picker with web-upload staging and clear feedback."""

from __future__ import annotations

from pathlib import Path
import uuid

import flet as ft

from core.config import settings
from core.theme import Colors, Radius, Spacing


class ImagePickerControl:
    """Select one image on desktop or web and expose its readable local path."""

    def __init__(self, page: ft.Page, label: str, current_url: str | None = None) -> None:
        self.page = page
        self.label = label
        self.selected_path: Path | None = None
        self._temporary_path: Path | None = None
        self._upload_name: str | None = None
        self.status = ft.Text(
            "Choose a JPEG, PNG, or WebP image up to 5 MB.",
            size=11,
            color=Colors.TEXT_SECONDARY,
        )
        self.progress = ft.ProgressBar(visible=False, color=Colors.PRIMARY)
        self.preview = ft.Container(
            width=82,
            height=104 if "cover" in label.lower() else 82,
            border_radius=Radius.MD,
            bgcolor=Colors.PRIMARY_MUTED,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            alignment=ft.alignment.center,
            content=ft.Image(src=current_url, fit=ft.ImageFit.COVER) if current_url else ft.Icon(ft.Icons.ADD_A_PHOTO_OUTLINED, color=Colors.PRIMARY),
        )
        # Flet 0.86 returns selected files from pick_files() instead of
        # sending an on_result event. Upload progress still uses on_upload.
        self.picker = ft.FilePicker(on_upload=self._uploaded)
        page.overlay.append(self.picker)
        self.control = ft.Container(
            bgcolor=Colors.SURFACE_ALT,
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.MD,
            padding=Spacing.MD,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.preview,
                    ft.Column(
                        expand=True,
                        tight=True,
                        spacing=Spacing.SM,
                        controls=[
                            ft.Text(label, weight=ft.FontWeight.W_600),
                            self.status,
                            self.progress,
                            ft.OutlinedButton("Choose image", icon=ft.Icons.UPLOAD_FILE_ROUNDED, on_click=self._choose),
                        ],
                    ),
                ],
            ),
        )

    @property
    def ready(self) -> bool:
        return self.selected_path is not None and self.selected_path.is_file()

    async def _choose(self, _event) -> None:
        files = await self.picker.pick_files(
            dialog_title=self.label,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            allow_multiple=False,
        )
        self._picked(files)

    def _picked(self, files) -> None:
        if not files:
            return
        selected = files[0]
        if selected.size and selected.size > 5 * 1024 * 1024:
            self.status.value = "Image is larger than 5 MB. Choose a smaller file."
            self.status.color = Colors.ERROR
            self.page.update()
            return
        local = Path(selected.path) if selected.path else None
        if local and local.is_file():
            self.selected_path = local
            self.status.value = f"Ready: {selected.name}"
            self.status.color = Colors.SUCCESS
            self.page.update()
            return

        suffix = Path(selected.name).suffix.lower()
        staged_name = f"image-{uuid.uuid4().hex}{suffix}"
        settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
        self._upload_name = selected.name
        self._temporary_path = settings.frontend_upload_directory / staged_name
        self.progress.visible = True
        self.status.value = f"Uploading {selected.name}…"
        self.status.color = Colors.PRIMARY
        self.page.update()
        try:
            upload_url = self.page.get_upload_url(staged_name, 600)
            self.picker.upload([
                ft.FilePickerUploadFile(name=selected.name, upload_url=upload_url)
            ])
        except Exception as exc:
            self.progress.visible = False
            self.status.value = "Image upload is not configured. Set FLET_SECRET_KEY and restart LIBRAI."
            self.status.color = Colors.ERROR
            self.page.update()

    def _uploaded(self, event) -> None:
        if event.error:
            self.progress.visible = False
            self.status.value = f"Upload failed: {event.error}"
            self.status.color = Colors.ERROR
        elif event.progress is not None:
            self.progress.value = event.progress
            if event.progress >= 1:
                self.progress.visible = False
                if self._temporary_path and self._temporary_path.is_file():
                    self.selected_path = self._temporary_path
                    self.status.value = "Image ready to save."
                    self.status.color = Colors.SUCCESS
                else:
                    self.status.value = "Upload finished, but the temporary file was not found."
                    self.status.color = Colors.ERROR
        self.page.update()

    def cleanup(self) -> None:
        """Remove only the web-upload staging file created by this control."""
        if self._temporary_path and self._temporary_path.is_file():
            root = settings.frontend_upload_directory.resolve()
            candidate = self._temporary_path.resolve()
            if root in candidate.parents:
                candidate.unlink()
