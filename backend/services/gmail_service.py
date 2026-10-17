"""Gmail HTTPS delivery using a privately stored, sender-authorized OAuth token."""
import base64
import json
from email import policy
from pathlib import Path

import httpx
from pydantic import EmailStr, TypeAdapter

TOKEN_URL = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
SCOPE = "https://www.googleapis.com/auth/gmail.send"


def load_credentials(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError()
        if data.get("type") != "authorized_user" or not all(isinstance(data.get(k), str) and data[k] for k in ("client_id", "client_secret", "refresh_token", "sender")):
            raise ValueError()
        TypeAdapter(EmailStr).validate_python(data["sender"])
        if SCOPE not in data.get("scopes", []):
            raise ValueError()
        return data
    except (OSError, ValueError, TypeError):
        raise ValueError("Gmail credentials are missing or invalid. Run the Gmail authorization command and configure GMAIL_OAUTH_FILE.") from None


def send_message(message, credentials: dict):
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        token = client.post(TOKEN_URL, data={"client_id":credentials["client_id"], "client_secret":credentials["client_secret"], "refresh_token":credentials["refresh_token"], "grant_type":"refresh_token"})
        if token.status_code != 200:
            raise ValueError("Gmail authorization failed. Reauthorize the sender; check OAuth publishing status and token expiry before retrying.")
        try:
            access_token = token.json()["access_token"]
            if not isinstance(access_token, str) or not access_token:
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise ValueError("Gmail returned an invalid authorization response. Reauthorize the sender before retrying.") from None
        encoded = base64.urlsafe_b64encode(message.as_bytes(policy=policy.SMTP)).decode("ascii")
        response = client.post(SEND_URL, headers={"Authorization":f"Bearer {access_token}"}, json={"raw":encoded})
        if response.status_code != 200:
            raise ValueError("Gmail did not confirm acceptance. Check send permission, sender restrictions and quotas before retrying; check Sent mail if the outcome is uncertain.")
        try:
            accepted = bool(response.json().get("id"))
        except (ValueError, AttributeError):
            accepted = False
        if not accepted:
            raise ValueError("Gmail returned no message ID. Check Sent mail before retrying to avoid a duplicate.")
