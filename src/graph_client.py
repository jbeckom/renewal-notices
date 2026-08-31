import os
import requests
import msal
import base64
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

CLIENT_ID = os.getenv("GRAPH_CLIENT_ID")
TENANT_ID = os.getenv("GRAPH_TENANT_ID")
CACHE_FILE = Path(".graph_token_cache.bin")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = [
    "User.Read",
    "Mail.ReadWrite.Shared",
    "Mail.Send",
]


def get_access_token() -> str:
    cache = load_cache()
    
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()

    result = None

    if accounts:
        result = app.acquire_token_silent(
            SCOPES,
            account=accounts[0]
        )

    if not result:
        result = app.acquire_token_interactive(scopes=SCOPES)

    save_cache(cache)

    if "access_token" not in result:
        raise RuntimeError("Could not acquire token: {result}")
    
    return result["access_token"]


def load_cache():
    cache = msal.SerializableTokenCache()

    if CACHE_FILE.exists():
        cache.deserialize(CACHE_FILE.read_text())

    return cache


def save_cache(cache):
    if cache.has_state_changed:
        CACHE_FILE.write_text(cache.serialize())


def graph_get(endpoint: str) -> dict:
    token = get_access_token()

    response = requests.get(
        f"https://graph.microsoft.com/v1.0{endpoint}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def graph_post(endpoint: str, payload: dict) -> dict:
    forbidden_send_endpoints = [
        "/sendMail",
        "/send"
    ]

    if any(blocked in endpoint for blocked in forbidden_send_endpoints):
        raise RuntimeError(f"Blocked unsafe Graph send endpoint: {endpoint}")

    token = get_access_token()

    response = requests.post(
        f"https://graph.microsoft.com/v1.0{endpoint}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    if response.text:
        return response.json()
    
    return {}


def create_shared_mailbox_draft(
        mailbox: str,
        to_email: str,
        subject: str,
        body: str,
) -> dict:
    payload = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body,
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_email,
                }
            }
        ],
    }

    return graph_post(
        f"/users/{mailbox}/messages",
        payload,
    )


def attach_file_to_message(
        mailbox: str,
        message_id: str,
        file_path: str | Path,
) -> dict:
    """
    Attach a file to an existing draft message.
    """

    file_path = Path(file_path)

    file_bytes = file_path.read_bytes()
    encoded_content = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": file_path.name,
        "contentType": "application/pdf",
        "contentBytes": encoded_content,
    }

    return graph_post(
        f"/users/{mailbox}/messages/{message_id}/attachments",
        payload,
    )


def create_shared_mailbox_draft_with_attachment (
        mailbox: str,
        to_email: str,
        subject: str,
        body: str,
        file_path: str | Path,
) -> dict:
    """
    Create a draft message with a required PDF attachment.

    The attachment is validated before the draft is created to avoid
    creating customer-facing drafts without renewal notices attached.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Attachment file not found: {file_path}")
    
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Attachment must be a PDF file: {file_path}")
    
    draft = create_shared_mailbox_draft(
        mailbox=mailbox,
        to_email=to_email,
        subject=subject,
        body=body
    )

    attachment = attach_file_to_message(
        mailbox=mailbox,
        message_id=draft["id"],
        file_path=file_path
    )

    return {
        "draft": draft,
        "attachment": attachment,
    }


def graph_get_all(endpoint: str) -> list[dict]:
    """
    Retrieve all pages from Microsoft Graph collection endpoint.
    """

    token = get_access_token()

    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    items = []

    while url:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()
        items.extend(data.get("value", []))

        url = data.get("@odata.nextLink")

    return items


def get_or_create_mail_folder(
        mailbox: str, 
        folder_name: str, 
) -> dict:
    """
    Return an existing root mail folder by display name,
    or create it if it doesn't already exist.
    """

    folders = graph_get_all(
        f"/users/{mailbox}/mailFolders"
        "?$select=id,displayName"
        "&$top=100"
    )

    for folder in folders:
        if folder.get("displayName", "").strip().lower() == folder_name.lower():
            return folder

    return graph_post(
        f"/users/{mailbox}/mailFolders",
        {
            "displayName": folder_name,
            "isHidden": False,
        },
    )


def move_message(
        mailbox: str,
        message_id: str,
        destination_folder_id: str,
) -> dict:
    """
    Move a message to another folder in the same mailbox.
    """

    return graph_post(
        f"/users/{mailbox}/messages/{message_id}/move",
        {
            "destinationId": destination_folder_id,
        },
    )