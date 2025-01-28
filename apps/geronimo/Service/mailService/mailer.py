import requests
from .auth import get_access_token
from .config import SERVICE_URL, API_KEY


def send_email_choreo(to_email, subject, body):
    access_token = get_access_token()
    print("Access Token: ", access_token)
    url = f"{SERVICE_URL}/emails"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Choreo-API-Key": API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "to": [to_email],
        "subject": subject,
        "body": body,
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise error for HTTP issues
    return response.json()
