"""Authorize one Gmail sender without displaying OAuth secrets or sending email."""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

import httpx
from pydantic import EmailStr, TypeAdapter
from backend.services.gmail_service import SCOPE, TOKEN_URL


def authorize(client_file: Path, sender: str, output: Path, *, timeout: int = 300):
    sender = str(TypeAdapter(EmailStr).validate_python(sender))
    if output.exists():
        raise ValueError("Output already exists. Choose a new --output path for reauthorization; do not overwrite a token still in use.")
    try:
        config = json.loads(client_file.read_text(encoding="utf-8-sig"))["installed"]
        client_id, client_secret = config["client_id"], config["client_secret"]
        if not client_id or not client_secret:
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError("Select the downloaded Desktop app OAuth client JSON.") from None
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    result = {}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # Callback URLs contain authorization codes.
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if urlparse(self.path).path != "/" or not secrets.compare_digest(query.get("state", [""])[0], state):
                self.send_response(400); self.end_headers(); return
            if query.get("error"):
                result["error"] = True
            elif query.get("code"):
                result["code"] = query["code"][0]
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store"); self.end_headers()
            self.wfile.write(b"LIBRAI received your response. Return to the terminal. You can close this tab.")
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        server.timeout = 1
        redirect = f"http://127.0.0.1:{server.server_port}/"
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({"client_id":client_id, "redirect_uri":redirect, "response_type":"code", "scope":SCOPE, "access_type":"offline", "prompt":"consent", "state":state, "code_challenge":challenge, "code_challenge_method":"S256", "login_hint":sender})
        print("Opening Google sign-in. Select the library sender and approve sending mail. No email is sent by this command.", flush=True)
        if not webbrowser.open(url):
            raise ValueError("Browser did not open. Run this command in your own VS Code terminal on the computer with your browser.")
        deadline = time.monotonic() + timeout
        while not result and time.monotonic() < deadline:
            server.handle_request()
        if not result.get("code"):
            raise ValueError("Google sign-in was declined or timed out. Check the sender is an OAuth test user, then run the command again.")
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(TOKEN_URL, data={"client_id":client_id, "client_secret":client_secret, "code":result["code"], "code_verifier":verifier, "redirect_uri":redirect, "grant_type":"authorization_code"})
        if response.status_code != 200:
            raise ValueError("Google token exchange failed. Check the Desktop client and consent configuration before retrying.")
        token = response.json()
        if not token.get("refresh_token") or SCOPE not in token.get("scope", "").split():
            raise ValueError("Google did not grant offline sending access. Review the consent settings and authorize again.")
    data = {"type":"authorized_user", "client_id":client_id, "client_secret":client_secret, "refresh_token":token["refresh_token"], "sender":sender, "scopes":[SCOPE]}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidentally replacing an existing sender token.
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as file:
        json.dump(data, file)
    print(f"GMAIL_AUTHORIZED: private credentials saved to {output}. No email was sent.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--sender", required=True)
    parser.add_argument("--output", type=Path, default=Path("generated/gmail-oauth.json"))
    args = parser.parse_args()
    try:
        authorize(args.client, args.sender, args.output)
    except Exception as exc:
        # Never print raw HTTP/JSON errors that could contain credentials.
        message = str(exc) if type(exc) is ValueError else "Authorization failed. Check the client file and network; no secrets were printed."
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
