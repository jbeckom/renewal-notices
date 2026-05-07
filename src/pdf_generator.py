from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def generate_test_pdf(record: dict, output_path: Path) -> None:
    """
    Generate a simple test PDF from one renewal record.

    This is intentionally basic.  The purpose is to verify that:
    - ReportLab works
    - A PDF file can be created
    - Record values can be written to the PDF
    """

    c = canvas.Canvas(str(output_path), pagesize=LETTER)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 720, "Renewal Notice - Test PDF")

    c.setFont("Helvetica", 10)

    y = 680
    for key, value in record.items():
        c.drawString(72, 7, f"{key}: {value}")
        y -= 18

    c.save()