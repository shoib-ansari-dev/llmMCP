"""
Session and CSRF Protection Middleware.
Provides session management and CSRF token validation.
"""

import secrets
import hashlib
import time
from typing import Dict, Optional, Any
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio


class SessionManager:
    """
    Simple in-memory session manager.
    """

    def __init__(self, session_ttl: int = 3600):
        """
        Initialize session manager.

        Args:
            session_ttl: Session time-to-live in seconds (default 1 hour)
        """
        self.session_ttl = session_ttl
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)

    def _generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        return hashlib.sha256(
            f"{session_id}:{secrets.token_hex(16)}".encode()
        ).hexdigest()[:32]

    async def create_session(self, client_ip: str) -> Dict[str, str]:
        """
        Create a new session.

        Returns:
            Dict with session_id and csrf_token
        """
        async with self._lock:
            session_id = self._generate_session_id()
            csrf_token = self._generate_csrf_token(session_id)

            self.sessions[session_id] = {
                "csrf_token": csrf_token,
                "client_ip": client_ip,
                "created_at": time.time(),
                "expires_at": time.time() + self.session_ttl,
                "data": {}
            }

            return {
                "session_id": session_id,
                "csrf_token": csrf_token
            }

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        async with self._lock:
            session = self.sessions.get(session_id)

            if not session:
                return None

            # Check if expired
            if time.time() > session["expires_at"]:
                del self.sessions[session_id]
                return None

            return session

    async def validate_csrf(self, session_id: str, csrf_token: str) -> bool:
        """Validate CSRF token for session."""
        session = await self.get_session(session_id)
        if not session:
            return False

        return secrets.compare_digest(session["csrf_token"], csrf_token)

    async def refresh_session(self, session_id: str) -> bool:
        """Refresh session expiry."""
        async with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["expires_at"] = time.time() + self.session_ttl
                return True
            return False

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    async def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        async with self._lock:
            now = time.time()
            expired = [
                sid for sid, session in self.sessions.items()
                if session["expires_at"] < now
            ]

            for sid in expired:
                del self.sessions[sid]

            return len(expired)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.
    Validates CSRF tokens on state-changing requests.
    """

    # Methods that require CSRF validation
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    # Paths exempt from CSRF (e.g., login, public APIs)
    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/session/create",
    }

    def __init__(self, app, session_manager: SessionManager, enabled: bool = True):
        super().__init__(app)
        self.session_manager = session_manager
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        # Skip if CSRF is disabled
        if not self.enabled:
            return await call_next(request)

        # Skip for safe methods
        if request.method not in self.PROTECTED_METHODS:
            return await call_next(request)

        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get session ID and CSRF token from headers
        session_id = request.headers.get("X-Session-ID")
        csrf_token = request.headers.get("X-CSRF-Token")

        if not session_id or not csrf_token:
            return Response(
                content='{"detail": "Missing session or CSRF token"}',
                status_code=403,
                media_type="application/json"
            )

        # Validate CSRF token
        is_valid = await self.session_manager.validate_csrf(session_id, csrf_token)

        if not is_valid:
            return Response(
                content='{"detail": "Invalid or expired CSRF token"}',
                status_code=403,
                media_type="application/json"
            )

        # Refresh session on valid request
        await self.session_manager.refresh_session(session_id)

        return await call_next(request)


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(session_ttl: int = 3600) -> SessionManager:
    """Get or create session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(session_ttl=session_ttl)
    return _session_manager

