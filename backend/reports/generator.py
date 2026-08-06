from __future__ import annotations
import csv
from pathlib import Path
from uuid import uuid4
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from backend.core.config import settings


def generate_report(report_type: str, format_: str, headers: list[str], rows: list[list]) -> Path:
    settings.report_directory.mkdir(parents=True, exist_ok=True)
    path=settings.report_directory/f"{report_type}-{uuid4().hex[:10]}.{format_}"
    if format_=="csv":
        with path.open("w",newline="",encoding="utf-8-sig") as f: writer=csv.writer(f);writer.writerow(headers);writer.writerows(rows)
    elif format_=="xlsx":
        wb=Workbook();ws=wb.active;ws.title=report_type[:31];ws.append(headers)
        for row in rows:ws.append(row)
        wb.save(path)
    else:
        pdf=canvas.Canvas(str(path),pagesize=A4);y=800;pdf.setFont("Helvetica-Bold",14);pdf.drawString(40,y,f"LIBRAI — {report_type.replace('_',' ').title()}");y-=28;pdf.setFont("Helvetica",8);pdf.drawString(40,y," | ".join(headers));y-=16
        for row in rows:
            pdf.drawString(40,y," | ".join(str(x)[:45] for x in row));y-=14
            if y<50:pdf.showPage();y=800;pdf.setFont("Helvetica",8)
        pdf.save()
    return path
