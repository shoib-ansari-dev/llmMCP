"""
Google OAuth Service
Handles Google OAuth authentication flow.
"""

import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from .config import get_auth_config
from .jwt import generate_state_token


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuth:
    """Google OAuth service."""

    def __init__(self):
        self.config = get_auth_config()

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = generate_state_token()

        params = {
            "client_id": self.config.google_client_id,
            "redirect_uri": self.config.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from Google

        Returns:
            Token response dict or None if failed
        """
        data = {
            "client_id": self.config.google_client_id,
            "client_secret": self.config.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.config.google_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)

            if response.status_code != 200:
                return None

            return response.json()

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from Google.

        Args:
            access_token: Google access token

        Returns:
            User info dict or None if failed
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(GOOGLE_USERINFO_URL, headers=headers)

            if response.status_code != 200:
                return None

            return response.json()

    async def authenticate(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Complete Google authentication flow.

        Args:
            code: Authorization code from Google callback

        Returns:
            Dict with user info or None if failed
        """
        # Exchange code for tokens
        tokens = await self.exchange_code(code)
        if not tokens:
            return None

        # Get user info
        access_token = tokens.get("access_token")
        if not access_token:
            return None

        user_info = await self.get_user_info(access_token)
        if not user_info:
            return None

        return {
            "google_id": user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "verified_email": user_info.get("verified_email", False)
        }


# Singleton instance
_google_oauth: Optional[GoogleOAuth] = None


def get_google_oauth() -> GoogleOAuth:
    """Get Google OAuth singleton."""
    global _google_oauth
    if _google_oauth is None:
        _google_oauth = GoogleOAuth()
    return _google_oauth

