import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FIELDPULSE_BASE_URL")

API_KEYS = {
    "an": os.getenv("FIELDPULSE_API_KEY_AN"),
    "mu": os.getenv("FIELDPULSE_API_KEY_MU"),
}


def get_headers(location: str) -> dict:
    """
    Build API request headers for a specific location.
    """

    api_key = API_KEYS.get(location.lower())

    if not api_key:
        raise ValueError(
            f"No API key configured for location: {location}"
        )
    
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }



def api_get(location: str, endpoint: str, params: dict | None = None) -> dict:
    """
    Make an authenticated GET request to the FieldPulse API.

    Args:
        location: Location code, such as 'an' or 'mu'
        endpoint: API endpoint path, such as '/version'
        params: Optional query string parameters

    Returns:
        Parsed JSON response
    """

    url = f"{BASE_URL}{endpoint}"

    response = requests.get(
        url,
        headers=get_headers(location),
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_customer(
        location: str,
        customer_id: str,
) -> dict:
    """
    Retrieve a customer by customer ID.
    """

    endpoint = f"/customers/{customer_id}"

    return api_get(location, endpoint)


def resolve_mailing_address(customer: dict) -> str | None:
    """
    Return the cusomter's billing address if FieldPulse indicates
    they have a different billing address.

    Returns None when the service/customer address should be used.
    """

    customer_data = customer.get("response", {})

    if not customer_data.get("has_different_billing_address"):
        return None
    
    address_1 = customer_data.get("billing_address_1")
    address_2 = customer_data.get("billing_address_2")
    city = customer_data.get("billing_city")
    state = customer_data.get("billing_state")
    zip_code = customer_data.get("billing_zip_code")

    lines = []

    if address_1:
        lines.append(address_1)

    if address_2:
        lines.append(address_2)

    city_state_zip = " ".join(
        part for part in [city, state, zip_code]
        if part
    )

    if city_state_zip:
        lines.append(city_state_zip)

    if not lines:
        return None
    
    return "\n".join(lines)

def enrich_record_with_mailing_address(record: dict) -> dict:
    """
    Enrich one renewal record with a mailing address override from FieldPulse.

    If FieldPulse indicates the customer has a different billing address,
    mailing_address is set to that billing address.

    If not, mailing_address remains None.
    """

    customer = get_customer(
        location=record["location"],
        customer_id=record["account_number"],
    )

    mailing_address = resolve_mailing_address(customer)

    record["mailing_address"] = mailing_address
    
    return record


def test_api_connection(location: str) -> None:
    """
    Test basic API connectivity and authentication.
    """

    print(f"Testing API connection for: {location.upper()}")

    data = api_get(location, "/version")

    print("Response JSON:")
    print(data)


if __name__ == "__main__":
    customer = get_customer(
        location="an",
        customer_id="14173777",
    )

    mailing_address = resolve_mailing_address(customer)

    print("Resolved mailing address:")
    print(mailing_address)