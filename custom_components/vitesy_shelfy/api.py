import time
import base64
import hashlib
import secrets
import logging
import requests
from urllib.parse import urlencode
from urllib.parse import quote

from .const import (
    LOGIN_URL,
    TOKEN_URL,
    CLIENT_ID,
    REDIRECT_URI,
    SCOPE,
    OAUTH_HEADERS,
    API_BASE_URL,
)

_LOGGER = logging.getLogger(__name__)

class VitesyOAuth:
    def __init__(self, email, password, session):
        self.email = email
        self.password = password
        self.session = session

        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.api_key = None

        self.code_verifier = self._generate_verifier()
        self.code_challenge = self._generate_challenge(self.code_verifier)

    def login(self):
        """Perform login and exchange tokens."""
        code = self._get_auth_code()
        if not code:
            raise Exception("Failed to get auth code")

        self._exchange_token(code)

    def _get_auth_code(self) -> str:
        session = requests.Session()

        # Step 1: GET login page to extract CSRF token and cookies
        query = {
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "response_type": "code",
            "state": secrets.token_hex(8),
            "nonce": secrets.token_hex(8),
            "scope": SCOPE,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
        }
        url = f"{LOGIN_URL}?{urlencode(query)}"
        response = session.get(url)
        if "XSRF-TOKEN" not in session.cookies:
            _LOGGER.error("CSRF token not found in cookies")
            return None

        csrf_token = session.cookies.get("XSRF-TOKEN")

        # Step 2: POST login with real CSRF token
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": url,
        }

        data = {
            "_csrf": csrf_token,
            "username": self.email,
            "password": self.password,
        }

        post_resp = session.post(url, headers=headers, data=data, allow_redirects=False)

        if "location" in post_resp.headers:
            location = post_resp.headers["location"]
            if "code=" in location:
                return location.split("code=")[1].split("&")[0]

        _LOGGER.error("Login failed: %s", post_resp.text)
        return None


    def _exchange_token(self, code: str):
        """Exchange authorization code for access and refresh tokens."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": self.code_verifier,
            "code": code,
        }

        resp = requests.post(TOKEN_URL, headers=OAUTH_HEADERS, data=payload)
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token")
            self.expires_at = time.time() + data.get("expires_in", 3600)
        else:
            raise Exception(f"Token exchange failed: {resp.status_code} {resp.text}")

    def refresh_access_token(self):
        """Use the refresh token to get a new access token."""
        payload = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": self.refresh_token,
        }

        resp = requests.post(TOKEN_URL, headers=OAUTH_HEADERS, data=payload)
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            self.expires_at = time.time() + data.get("expires_in", 3600)
        else:
            raise Exception(f"Refresh token failed: {resp.status_code} {resp.text}")

    def _auth_headers(self):
        if self.is_token_expired():
            self.refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
    def get_devices(self):
        url = f"{API_BASE_URL}/devices?user_id=me&connected_once=true&expand=all%2C-place"
        resp = requests.get(url, headers=self._auth_headers())
        resp.raise_for_status()
        return resp.json()

    def get_measurements(self, device_id):
        encoded_device_id = quote(device_id, safe='')
        url = f"{API_BASE_URL}/measurements?device_id={encoded_device_id}&latest=true"
        resp = requests.get(url, headers=self._auth_headers())
        resp.raise_for_status()
        return resp.json()

    def get_maintenance(self, device_id):
        encoded_device_id = quote(device_id, safe='')
        url = f"{API_BASE_URL}/devices/{device_id}/maintenance"
        resp = requests.get(url, headers=self._auth_headers())
        resp.raise_for_status()
        return resp.json()

    def get_programs(self, device_type, firmware_version):
        url = f"{API_BASE_URL}/programs/?device_type={device_type}&firmware_version={firmware_version}"
        resp = requests.get(url, headers=self._auth_headers())
        resp.raise_for_status()
        return resp.json()

    def reset_filter(self, device_id):
        """Reset the filter maintenance period for a device."""
        url = f"{API_BASE_URL}/devices/{device_id}/maintenance/filter/done"
        headers = self._auth_headers()
        headers.update({
            "Accept-Language": "it-IT",
            "Accept-Encoding": "gzip",
            "User-Agent": "VitesyHub/5.3.10 (Android; HomeAssistant)",
            "Connection": "Keep-Alive",
        })
        resp = requests.post(url, headers=headers)  # niente body
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "text": resp.text}

    def reset_fridge(self, device_id):
        """Reset the filter maintenance period for a device."""
        url = f"{API_BASE_URL}/devices/{device_id}/maintenance/fridge/done"
        headers = self._auth_headers()
        headers.update({
            "Accept-Language": "it-IT",
            "Accept-Encoding": "gzip",
            "User-Agent": "VitesyHub/5.3.10 (Android; HomeAssistant)",
            "Connection": "Keep-Alive",
        })
        resp = requests.post(url, headers=headers)  # niente body
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "text": resp.text}
        
    def get_or_create_api_key(self):
        """Get existing API key or create a new one if not present."""
        url = f"{API_BASE_URL}/users/me/api-key"
        headers = self._auth_headers()

        # Try GET first
        resp = requests.get(url, headers=headers)
        data = resp.json()

        if "apiKey" in data:
            self.api_key = data["apiKey"]
            return self.api_key

        # If no apiKey and specific error, try POST
        if data.get("error", {}).get("message") == "User does not have ApiKey":
            post_resp = requests.post(url, headers=headers)
            post_data = post_resp.json()
            if "apiKey" in post_data:
                self.api_key = post_data["apiKey"]
                return self.api_key
            else:
                raise Exception(f"Failed to create ApiKey: {post_data}")
        else:
            raise Exception(f"Unexpected error fetching ApiKey: {data}")
                 
    def is_token_expired(self):
        return time.time() >= (self.expires_at or 0)

    @staticmethod
    def _generate_verifier() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _generate_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")
