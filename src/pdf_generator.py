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


def draw_wrapped_text(c, x, y, text, max_width, line_height=14):
    """
    Draw text that wraps within a maximum width.

    This is useful for paragraphs where the text should stay within the page margins instead of running off the page.
    """

    words = text.split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()

        if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        c.drawString(x, y, line)
        y -= line_height

    return y


def generate_renewal_notice_pdf(record: dict, output_path: Path, company_info: dict, logo_path: Path) -> None:
    """
    Generate a structured renewal notice PDF.

    This version focuses on layout structure only.
    Styling and branding will be added later.
    """

    c = canvas.Canvas(str(output_path), pagesize=LETTER)

    width, height = LETTER

    # --------------------------------------------------
    # LAYOUT CONSTANTS
    # --------------------------------------------------

    LOGO_Y = 702
    BODY_OFFSET = 0

    # --------------------------------------------------
    # COMPANY HEADER
    # --------------------------------------------------

    if logo_path.exists():
        c.drawImage(
            str(logo_path),
            x=106,
            y=LOGO_Y,
            width=400,
            height=78,
            preserveAspectRatio=True,
            mask="auto"
        )
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(
            width / 2,
            760,
            company_info["name"]
        )

    c.setFont("Helvetica", 9)

    c.drawCentredString(
        width / 2,
        692,
        company_info["address"]
    )

    c.drawCentredString(
        width / 2,
        680,
        f"{company_info['phone']} | {company_info['website']}"
    )

    # --------------------------------------------------
    # NOTICE TITLE
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 24)

    c.drawCentredString(
        width / 2,
        642,
        "RENEWAL NOTICE"
    )

    # --------------------------------------------------
    # ACCOUNT INFO
    # --------------------------------------------------

    c.setFont("Helvetica", 12)

    c.drawString(
        72,
        617,
        f"Account #: {record['account_number']}"
    )

    c.drawRightString(
        width - 72,
        617,
        f"Date: {record['run_date']}"
    )

    # --------------------------------------------------
    # CUSTOMER INFO/ADDRESS BOX
    # --------------------------------------------------

    box_x = 72
    box_y = 534
    box_width = 468
    box_height = 75
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
        record.get("mailing_address") or record["service_address"]
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
    # NOTICE MESSAGE
    # --------------------------------------------------

    message_y = box_y - 30

    c.setFont("Helvetica", 10)

    message = (
        "Our records indicate that your current Safety & Comfort Agreement is coming up "
        "for renewal. Please review the renewal details below and contact us with "
        "any questions."
    )

    after_message_y = draw_wrapped_text(
        c,
        72,
        message_y,
        message,
        max_width=468,
    )

    # --------------------------------------------------
    # AGREEMENT / PAYMENT SECTION
    # --------------------------------------------------

    agreement_y = after_message_y - 20

    left_x = 72
    right_x = 360

    c.setFont("Helvetica-Bold", 11)

    c.drawString(
        left_x,
        agreement_y,
        f"Renewal for Agreement #: {record['agreement_id']}"
    )

    c.drawString(
        right_x,
        agreement_y,
        f"Payment Due Date: {record['payment_due_date']}"
    )

    c.setFont("Helvetica", 10)

    c.drawString(
        left_x,
        agreement_y - 22,
        f"Agreement Type: {record['agreement_type']}"
    )

    c.drawString(
        left_x,
        agreement_y - 42,
        f"Coverage Through: {record['coverage_through']}"
    )

    c.drawString(
        left_x,
        agreement_y - 62,
        f"Total Agreement Price: {record['total_price']}"
    )

    c.setFont("Helvetica-Bold", 11)

    c.drawString(
        right_x,
        agreement_y - 22,
        f"Amount Due: {record['total_price']}"
    )

    # --------------------------------------------------
    # REMITTANCE SECTION
    # --------------------------------------------------

    REMITTANCE_Y = 170
    margin_x = 72

    separator_text = (
        "Please detach and return this section with your payment."
    )

    c.setFont("Helvetica-Oblique", 9)

    text_width = c.stringWidth(
        separator_text,
        "Helvetica-Oblique",
        9
    )

    text_x = (width - text_width) / 2

    line_y = REMITTANCE_Y + 3
    gap = 8

    # Left dashed line
    c.setDash(3, 3)

    c.line(
        margin_x,
        line_y,
        text_x - gap,
        line_y
    )

    # Right dashed line
    c.line(
        text_x + text_width + gap,
        line_y,
        width - margin_x,
        line_y
    )

    # Reset dash pattern
    c.setDash()

    # Separator text
    c.drawString(
        text_x,
        REMITTANCE_Y,
        separator_text
    )

    remit_y = REMITTANCE_Y - 35

    c.setFont("Helvetica-Bold", 10)

    c.drawString(
        72,
        remit_y,
        f"Account #: {record['account_number']}"
    )

    c.drawRightString(
        width - 72,
        remit_y,
        f"Agreement #: {record['agreement_id']}"
    )

    c.setFont("Helvetica", 10)

    c.drawString(
        72,
        remit_y - 20,
        f"Customer: {record['customer_name'].split(chr(10))[0]}"
    )

    c.drawString(
        72,
        remit_y - 45,
        f"Amount Due: {record['total_price']}"
    )

    c.setFont("Helvetica-Bold", 10)

    c.drawString(
        72,
        remit_y - 80,
        "Make checks payable to:"
    )

    c.setFont("Helvetica", 10)

    c.drawString(
        72,
        remit_y - 100,
        # company_info["name"]
        "Summers of Anderson, Inc"
    )

    # --------------------------------------------------
    # SAVE PDF
    # --------------------------------------------------

    c.save()



### TESTING ONLY ###
if __name__ == "__main__":
    from datetime import date

    COMPANY_INFO = {
        "AN": {
            "name": "Summers Plumbing Heating & Cooling",
            "address": "3423 Columbus Ave, Anderson, IN 46013",
            "phone": "765.644.4328",
            "website": "www.summersphc.com"
        },
        "MU": {
            "name": "Summers Plumbing Heating & Cooling",
            "address": "3700 S Hoyt Ave, Muncie, IN 47302",
            "phone": "765.399.4328",
            "website": "www.summersphc.com"
        }
    }

    test_record = {
        "agreement_id": "10980",
        "customer_name": "Michael Mendoza",
        "mailing_address": (
            "123 Billing Street\n"
            "Indianapolis, Indiana 46204"
        ),
        "service_address": (
            "2214 Meridian Street\n"
            "Anderson, Indiana 46016"
        ),
        "run_date": date.today().strftime("%-m/%-d/%Y"),
        "coverage_through": "6/3/2026",
        "agreement_type": "MAINTW/JOB",
        "expiration_date": "6/2/2027",
        "agreement_price": "$149.00",
        "total_price": "$149.00",
        "payment_due_date": "6/3/2026",
        "account_number": "14173313",
        "renewal_date": "5/7/2026",
        "location": "an",
    }


    generate_renewal_notice_pdf(
        record = test_record,
        logo_path=Path("templates/SPHC-Logo-BlkText--.png"),
        output_path=Path("output/test/demo.pdf"),
        company_info=COMPANY_INFO["AN"],
    )