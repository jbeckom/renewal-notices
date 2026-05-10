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
    Make an authenticated GET request to the FieldPusle API.

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


def get_customer_billing_address(customer: dict) -> dict:
    """
    Determine which sutomer address should be used 
    for renewal notice billing purposes.
    """

    customer_data = customer["response"]

    if customer_data.get("has_different_billing_address"):
        return {
            "address_1": customer_data.get("billing_address_1"),
            "address_2": customer_data.get("billing_address_2"),
            "city": customer_data.get("billing_city"),
            "state": customer_data.get("billing_state"),
            "zip_code": customer_data.get("billing_zip_code"),
        }
    
    return {
        "address_1": customer_data.get("address_1"),
        "address_2": customer_data.get("address_2"),
        "city": customer_data.get("city"),
        "state": customer_data.get("state"),
        "zip_code": customer_data.get("zip_code"),
    }


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
        customer_id="14175586",
    )

    print(json.dumps(customer, indent=4))