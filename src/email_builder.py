import config as cfg


def build_email_body(record: dict, company_info: dict) -> str:
    """
    Build the customer-facing renewal email body.
    """

    customer_name = record.get("customer_name", "").split("\n")[0]
    coverage_through = record.get("coverage_through")
    total_price = record.get("total_price")
    payment_due_date = record.get("payment_due_date")

    return(
        f"Hello {customer_name},\n\n"
        "Your Safety & Comfort Membership is coming up for renewal. "
        "We've attached your renewal notice with the coverage details, "
        "renewal date, and amount due.\n\n"
        f"Coverage Through: {coverage_through}\n"
        f"Payment Due Date: {payment_due_date}\n"
        f"Amount Due: {total_price}\n\n"
        "Please review the attached notice and contact our office if you "
        "have any questions or would like to make a payment by phone.\n\n"
        "Thank you for choosing Summers Plumbing Heating & Cooling.\n\n"
        "Summers Plumbing Heating & Cooling\n"
        f"{company_info['phone']}"
    )


def build_email_queue_values(record: dict, pdf_path, company_info:dict) -> dict:
    """
    Determine email queue values for one renewal record.
    """

    email = record.get("email")

    if email:
        delivery_method = "EMAIL"
        status = "READY"
    else:
        delivery_method = "PRINT_MAIL"
        status = "MISSING_EMAIL"

    return {
        "subject": cfg.EMAIL_SUBJECT,
        "body": build_email_body(record, company_info),
        "delivery_method": delivery_method,
        "status": status
    }