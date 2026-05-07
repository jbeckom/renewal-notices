from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def draw_multiline_text(c, x, y, text, line_height=14):
    """
    Draw text containing line breaks.

    Args:
        c: ReportLab canvas
        x: X coordinate
        y: Starting Y coordinate
        text: Text to draw
        line_height: Space between lines

    Returns:
        Updated Y position after drawing
    """

    for line in str(text).split("\n"):
        c.drawString(x, y, line)
        y -= line_height

    return y


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
        c.drawString(72, y, f"{key}: {value}")
        y -= 18

    c.save()


def generate_renewal_notice_pdf(record: dict, output_path: Path, company_info: dict) -> None:
    """
    Generate a structured renewal notice PDF.

    This version focuses on layout structure only.
    Styling and branding will be added later.
    """

    c = canvas.Canvas(str(output_path), pagesize=LETTER)

    width, height = LETTER

    TOP_OFFSET = -40

    # --------------------------------------------------
    # COMPANY HEADER
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, 760, company_info["name"])

    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 746, company_info["address"])
    c.drawCentredString(
        width / 2,
        732,
        f"{company_info['phone']} | {company_info['website']}"
    )

    # --------------------------------------------------
    # NOTICE TITLE
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, 700, "Renewal Notice")

    # --------------------------------------------------
    # ACCOUNT INFO
    # --------------------------------------------------

    c.setFont("Helvetica", 10)

    c.drawString(
        72,
        670 + TOP_OFFSET,
        f"Account #: {record['account_number']}"
    )

    c.drawRightString(
        width - 72,
        670 + TOP_OFFSET,
        f"Date: {record['run_date']}"
    )

    # --------------------------------------------------
    # CUSTOMER INFO/ADDRESS BOX
    # --------------------------------------------------

    box_x = 72
    box_y = 540 + TOP_OFFSET
    box_width = 468
    box_height = 110
    divider_x = box_x + (box_width / 2)

    left_x = box_x + 10
    right_x = divider_x + 10
    text_top_y = box_y + box_height -20

    # Outer box
    c.rect(box_x, box_y, box_width, box_height)

    c.setFont("Helvetica", 10)

    # Left side: customer/billing placeholder
    left_y = draw_multiline_text(
        c,
        left_x,
        text_top_y,
        record['customer_name']
    )

    draw_multiline_text(
        c,
        left_x,
        left_y,
        record['service_address']
    )

    # Right side: service address
    c.drawString(right_x, text_top_y, "Service Address:")

    draw_multiline_text(
        c,
        right_x,
        text_top_y - 20,
        record['service_address']
    )

    # --------------------------------------------------
    # AGREEMENT SECTION
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 11)

    c.drawString(
        72,
        530 + TOP_OFFSET,
        f"Renewal for Agreement #: {record['agreement_id']}"
    )

    c.setFont("Helvetica", 10)

    c.drawString(
        72,
        490 + TOP_OFFSET,
        f"Agreement Type: {record['agreement_type']}"
    )

    c.drawString(
        72,
        465 + TOP_OFFSET,
        f"Coverage Through: {record['coverage_through']}"
    )

    c.drawString(
        72,
        440 + TOP_OFFSET,
        f"Total Agreement Price: {record['total_price']}"
    )

    # --------------------------------------------------
    # PAYMENT SECTION
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 11)

    c.drawString(
        72,
        390 + TOP_OFFSET,
        f"Payment Due Date: {record['payment_due_date']}"
    )

    c.drawString(
        72,
        365 + TOP_OFFSET,
        f"Amount Due: {record['total_price']}"
    )

    # --------------------------------------------------
    # SAVE PDF
    # --------------------------------------------------

    c.save()