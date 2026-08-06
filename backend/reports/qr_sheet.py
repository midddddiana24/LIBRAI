"""Printable A4 QR label sheets for accessioned library copies."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from backend.core.config import settings


def generate_book_qr_sheet(book, copies) -> Path:
    settings.report_directory.mkdir(parents=True, exist_ok=True)
    path = settings.report_directory / f"book-{book.id}-qr-labels-{uuid4().hex[:10]}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    page_width, page_height = A4
    margin = 34
    gap = 10
    columns, rows_per_page = 2, 4
    cell_width = (page_width - margin * 2 - gap) / columns
    cell_height = (page_height - margin * 2 - gap * 3) / rows_per_page

    for index, copy in enumerate(copies):
        position = index % (columns * rows_per_page)
        if index and position == 0:
            pdf.showPage()
        row, column = divmod(position, columns)
        x = margin + column * (cell_width + gap)
        y = page_height - margin - (row + 1) * cell_height - row * gap
        pdf.setStrokeColorRGB(0.86, 0.89, 0.92)
        pdf.roundRect(x, y, cell_width, cell_height, 8, stroke=1, fill=0)

        image = qrcode.make(copy.qr_token)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        qr_size = 112
        pdf.drawImage(ImageReader(buffer), x + 14, y + (cell_height - qr_size) / 2, qr_size, qr_size, preserveAspectRatio=True, mask="auto")
        text_x = x + 140
        pdf.setFillColorRGB(0.07, 0.20, 0.31)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(text_x, y + cell_height - 35, "LIBRAI")
        pdf.setFillColorRGB(0.10, 0.13, 0.17)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(text_x, y + cell_height - 57, str(copy.accession_number)[:25])
        pdf.setFont("Helvetica", 8)
        title = str(book.title)
        pdf.drawString(text_x, y + cell_height - 76, title[:30])
        if len(title) > 30:
            pdf.drawString(text_x, y + cell_height - 89, title[30:60])
        pdf.setFillColorRGB(0.35, 0.40, 0.46)
        pdf.setFont("Helvetica", 7)
        pdf.drawString(text_x, y + 24, "Scan at the library kiosk")

    pdf.save()
    return path
