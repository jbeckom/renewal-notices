import os
import requests
import msal
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
            "contentType": "Text",
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


if __name__ == "__main__":
    # me = graph_get("/me")
    # print(me)

    # mailbox = graph_get(
    #     "/users/renewals@an.summersphc.com/mailFolders"
    # )

    draft = create_shared_mailbox_draft(
        mailbox=os.getenv("GRAPH_SHARED_MAILBOX"),
        to_email="jbeckom@gmail.com",
        subject="Test renewal draft",
        body="This is a test draft created by the renewal notice automation project."
    )

    print(draft)