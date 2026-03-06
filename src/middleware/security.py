"""
Security Module
Same-site validation, CORS, and origin checking.
"""

import os
from typing import Optional, Set
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re


class SameSiteValidator:
    """
    Validates that requests come from allowed origins only.
    Ensures frontend-only access to backend API.
    """

    def __init__(
        self,
        allowed_origins: Optional[Set[str]] = None,
        allowed_hosts: Optional[Set[str]] = None,
        enforce: bool = True
    ):
        """
        Initialize same-site validator.

        Args:
            allowed_origins: Set of allowed Origin header values
            allowed_hosts: Set of allowed Host header values
            enforce: If True, reject requests from unknown origins
        """
        self.enforce = enforce

        # Load from environment or use provided values
        env_origins = os.getenv("ALLOWED_ORIGINS", "")
        env_hosts = os.getenv("ALLOWED_HOSTS", "")

        self.allowed_origins = allowed_origins or set(
            o.strip() for o in env_origins.split(",") if o.strip()
        )

        self.allowed_hosts = allowed_hosts or set(
            h.strip() for h in env_hosts.split(",") if h.strip()
        )

        # Add defaults for development
        if not self.allowed_origins:
            self.allowed_origins = {
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            }

        if not self.allowed_hosts:
            self.allowed_hosts = {
                "localhost",
                "localhost:8000",
                "127.0.0.1",
                "127.0.0.1:8000",
            }

    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return True  # Same-origin requests don't have Origin header

        # Check exact match
        if origin in self.allowed_origins:
            return True

        # Check wildcard patterns
        for allowed in self.allowed_origins:
            if allowed.startswith("*."):
                # Wildcard subdomain match
                domain = allowed[2:]
                if origin.endswith(domain) or origin.endswith(f"://{domain}"):
                    return True

        return False

    def is_host_allowed(self, host: Optional[str]) -> bool:
        """Check if host is allowed."""
        if not host:
            return False

        # Remove port for comparison if checking without port
        host_without_port = host.split(":")[0]

        return host in self.allowed_hosts or host_without_port in self.allowed_hosts

    def is_referer_valid(self, referer: Optional[str], origin: Optional[str]) -> bool:
        """Check if referer matches origin."""
        if not referer:
            return True

        # Extract origin from referer
        try:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            referer_origin = f"{parsed.scheme}://{parsed.netloc}"

            if origin and referer_origin != origin:
                return False

            return self.is_origin_allowed(referer_origin)
        except Exception:
            return False


class SameSiteMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce same-site policy.
    Only allows requests from configured frontend origins.
    """

    # Paths exempt from same-site checking
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # Methods that require origin checking
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    def __init__(self, app, validator: Optional[SameSiteValidator] = None):
        super().__init__(app)
        self.validator = validator or SameSiteValidator()

    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip if not enforcing
        if not self.validator.enforce:
            return await call_next(request)

        # Get headers
        origin = request.headers.get("Origin")
        host = request.headers.get("Host")
        referer = request.headers.get("Referer")

        # Validate host
        if not self.validator.is_host_allowed(host):
            return Response(
                content='{"detail": "Invalid host"}',
                status_code=403,
                media_type="application/json"
            )

        # For state-changing requests, validate origin
        if request.method in self.PROTECTED_METHODS:
            if origin and not self.validator.is_origin_allowed(origin):
                return Response(
                    content='{"detail": "Origin not allowed"}',
                    status_code=403,
                    media_type="application/json"
                )

            # Validate referer
            if not self.validator.is_referer_valid(referer, origin):
                return Response(
                    content='{"detail": "Invalid referer"}',
                    status_code=403,
                    media_type="application/json"
                )

        # Add security headers to response
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


def get_cors_origins() -> list:
    """Get CORS origins from environment."""
    env_origins = os.getenv("ALLOWED_ORIGINS", "")

    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]

    # Default development origins
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


def get_same_site_validator() -> SameSiteValidator:
    """Create same-site validator from environment."""
    enforce = os.getenv("SAME_SITE_ENFORCE", "true").lower() == "true"
    return SameSiteValidator(enforce=enforce)

