import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv
from graph_client import create_shared_mailbox_draft_with_attachment

load_dotenv()


if __name__ == "__main__":
    mailbox = os.getenv("GRAPH_SHARED_MAILBOX")

    result = create_shared_mailbox_draft_with_attachment(
        mailbox=mailbox,
        to_email="jbeckom@gmail.com",
        subject="Test renewal draft with attachment",
        body="This is a test draft with a PDF attachment",
        file_path="output/2606/mu/2606-renewal-mu-6513-sue-davis.pdf",
    )

    print("Draft created:", result["draft"]["id"])
    print("Attachment added:", result["attachment"].get("name"))