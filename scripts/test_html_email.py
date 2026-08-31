import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from email_builder import build_email_body_html

sample_record = {
    "customer_name": "ACME Plumbing\nAttn: Sarah Johnson",
    "agreement_id": "12345",
    "agreement_type": "1YRMAINT",
    "expiration_date": "06/30/2026",
    "total_price": "$999.00",
    "location": "MU"
}


if __name__ == "__main__":
    html = build_email_body_html(sample_record)

    output_path = Path("output/test_email_preview.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"HTML email preview written to: {output_path}")