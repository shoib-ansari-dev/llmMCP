"""
Rate Limiter Middleware
IP-based rate limiting for API requests.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio


class RateLimiter:
    """
    IP-based rate limiter.
    Limits requests per IP to a configurable rate.
    """

    def __init__(self, requests_per_minute: int = 1):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for given IP.

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_size

            # Clean old requests outside the window
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]

            # Check if under limit
            if len(self.requests[client_ip]) < self.requests_per_minute:
                self.requests[client_ip].append(current_time)
                return True, 0

            # Calculate retry after
            oldest_request = min(self.requests[client_ip])
            retry_after = int(oldest_request + self.window_size - current_time) + 1

            return False, max(retry_after, 1)

    def reset(self, client_ip: str = None):
        """Reset rate limit for IP or all IPs."""
        if client_ip:
            self.requests.pop(client_ip, None)
        else:
            self.requests.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
        "/status",
    }

    def __init__(self, app, requests_per_minute: int = 1):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self.get_client_ip(request)
        is_allowed, retry_after = await self.limiter.is_allowed(client_ip)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.limiter.requests_per_minute - len(self.limiter.requests.get(client_ip, []))
        )

        return response


# Singleton instance
_rate_limiter: RateLimiter = None


def get_rate_limiter(requests_per_minute: int = 1) -> RateLimiter:
    """Get or create rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)
    return _rate_limiter

