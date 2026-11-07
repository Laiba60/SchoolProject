"""PDF report card: school logo in the header, faded logo + diagonal school name as watermark."""
import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from results.services import student_report
from school.models import SiteSettings

NAVY = colors.HexColor("#1e3a8a")
DEFAULT_LOGO = Path(__file__).parent / "assets" / "logo.png"


def _logo_path(site):
    try:
        if site.logo and Path(site.logo.path).exists():
            return site.logo.path
    except ValueError:
        pass
    return str(DEFAULT_LOGO)


def build_report(student):
    site = SiteSettings.load()
    logo, school, data = ImageReader(_logo_path(site)), site.school_name, student_report(student)
    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=48 * mm, bottomMargin=20 * mm, title=f"Result - {student.full_name}")

    def page(c, _doc):
        w, h = A4
        c.saveState()  # watermark
        c.setFillAlpha(0.07)
        c.drawImage(logo, w / 2 - 70 * mm, h / 2 - 70 * mm, 140 * mm, 140 * mm, mask="auto")
        c.translate(w / 2, h / 2)
        c.rotate(35)
        c.setFont("Helvetica-Bold", 34)
        c.setFillColor(colors.Color(30 / 255, 58 / 255, 138 / 255, alpha=0.10))  # set after, it carries its own alpha
        c.drawCentredString(0, -10, school.upper())
        c.restoreState()
        c.saveState()  # header
        c.drawImage(logo, 20 * mm, h - 38 * mm, 22 * mm, 22 * mm, mask="auto")
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(NAVY)
        c.drawString(47 * mm, h - 26 * mm, school.upper())
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        c.drawString(47 * mm, h - 33 * mm, "Official Result Card")
        c.setStrokeColor(NAVY)
        c.line(20 * mm, h - 41 * mm, w - 20 * mm, h - 41 * mm)
        c.restoreState()

    p = data["profile"]
    story = [
        Paragraph(f"<b>Student Name:</b> {escape(p['full_name'])} &nbsp;|&nbsp; <b>Roll No:</b> {escape(p['uid'])}", styles["Normal"]),
        Spacer(1, 2 * mm),
        Paragraph(f"<b>Class / Section:</b> {escape(p['section'])} &nbsp;|&nbsp; <b>Father Name:</b> {escape(p['father_name'])}", styles["Normal"]),
    ]
    if p.get("term"):
        story += [Spacer(1, 2 * mm), Paragraph(f"<b>Term:</b> {escape(p['term'])}", styles["Normal"])]
    story.append(Spacer(1, 8 * mm))
    rows = [["Subject", "Total", "Obtained", "%", "Grade"]]
    rows += [[r["subject"], r["total_marks"], r["obtained_marks"], f"{r['percentage']:g}%", r["grade"]] for r in data["results"]]
    rows.append(["TOTAL", data["total_marks"], data["obtained_marks"], f"{data['percentage']:g}%", data["grade"]])
    t = Table(rows, colWidths=[70 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)
    if not data["results"]:
        story += [Spacer(1, 6 * mm), Paragraph("No results have been uploaded yet.", styles["Normal"])]
    doc.build(story, onFirstPage=page, onLaterPages=page)
    return buf.getvalue()
