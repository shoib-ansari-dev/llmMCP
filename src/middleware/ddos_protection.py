"""
DDoS Protection Middleware
Detects and blocks suspicious request patterns across different IPs.
Uses request fingerprinting to identify similar requests.
"""

import hashlib
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, field

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RequestPattern:
    """Tracks a request pattern across IPs."""
    count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    ips: set = field(default_factory=set)
    blocked: bool = False
    blocked_at: Optional[float] = None


class DDoSProtection:
    """
    DDoS protection using request fingerprinting.

    Detects patterns like:
    - Same endpoint + method + similar payload from multiple IPs
    - Rapid requests with same user-agent from different IPs
    - Identical request signatures across IP addresses
    """

    def __init__(
        self,
        pattern_threshold: int = 5,  # Block after N similar requests
        time_window: int = 60,  # Time window in seconds
        block_duration: int = 300,  # Block duration in seconds (5 min)
        cleanup_interval: int = 120,  # Cleanup old patterns every N seconds
    ):
        self.pattern_threshold = pattern_threshold
        self.time_window = time_window
        self.block_duration = block_duration
        self.cleanup_interval = cleanup_interval

        # Pattern storage: fingerprint -> RequestPattern
        self._patterns: Dict[str, RequestPattern] = defaultdict(RequestPattern)

        # Blocked fingerprints
        self._blocked_fingerprints: Dict[str, float] = {}

        # Last cleanup time
        self._last_cleanup = time.time()

    def _generate_fingerprint(
        self,
        method: str,
        path: str,
        user_agent: str,
        content_type: Optional[str],
        body_hash: Optional[str],
        query_params: str
    ) -> str:
        """
        Generate a fingerprint for the request.
        Combines multiple factors to identify similar requests.
        """
        # Create fingerprint components
        components = [
            method.upper(),
            path.lower(),
            # Normalize user-agent (take first 50 chars to handle minor variations)
            (user_agent or "")[:50].lower(),
            content_type or "",
            body_hash or "",
            query_params
        ]

        # Create hash of components
        fingerprint_str = "|".join(components)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

    def _generate_body_hash(self, body: bytes) -> str:
        """Generate a hash of the request body."""
        if not body:
            return ""
        # Hash the body content
        return hashlib.md5(body).hexdigest()[:16]

    def _cleanup_old_patterns(self):
        """Remove expired patterns and unblock expired fingerprints."""
        current_time = time.time()

        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        self._last_cleanup = current_time

        # Clean up old patterns
        expired_patterns = []
        for fingerprint, pattern in self._patterns.items():
            if current_time - pattern.last_seen > self.time_window * 2:
                expired_patterns.append(fingerprint)

        for fp in expired_patterns:
            del self._patterns[fp]

        # Clean up expired blocks
        expired_blocks = []
        for fingerprint, blocked_at in self._blocked_fingerprints.items():
            if current_time - blocked_at > self.block_duration:
                expired_blocks.append(fingerprint)

        for fp in expired_blocks:
            del self._blocked_fingerprints[fp]
            # Also reset the pattern
            if fp in self._patterns:
                self._patterns[fp].blocked = False
                self._patterns[fp].count = 0
                self._patterns[fp].ips.clear()

        if expired_patterns or expired_blocks:
            logger.debug(
                f"DDoS cleanup: removed {len(expired_patterns)} patterns, "
                f"unblocked {len(expired_blocks)} fingerprints"
            )

    def check_request(
        self,
        ip: str,
        method: str,
        path: str,
        user_agent: str,
        content_type: Optional[str] = None,
        body: Optional[bytes] = None,
        query_params: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a request should be blocked.

        Returns:
            Tuple of (is_blocked, reason)
        """
        self._cleanup_old_patterns()

        current_time = time.time()
        body_hash = self._generate_body_hash(body) if body else ""

        fingerprint = self._generate_fingerprint(
            method, path, user_agent, content_type, body_hash, query_params
        )

        # Check if fingerprint is already blocked
        if fingerprint in self._blocked_fingerprints:
            blocked_at = self._blocked_fingerprints[fingerprint]
            if current_time - blocked_at < self.block_duration:
                remaining = int(self.block_duration - (current_time - blocked_at))
                return True, f"Request pattern blocked. Try again in {remaining}s"
            else:
                # Block expired, remove it
                del self._blocked_fingerprints[fingerprint]

        # Get or create pattern
        pattern = self._patterns[fingerprint]

        # Check if this is within the time window
        if current_time - pattern.first_seen > self.time_window:
            # Reset pattern for new time window
            pattern.count = 0
            pattern.ips.clear()
            pattern.first_seen = current_time

        # Update pattern
        pattern.count += 1
        pattern.last_seen = current_time
        pattern.ips.add(ip)

        # Check if threshold exceeded from multiple IPs
        if pattern.count >= self.pattern_threshold and len(pattern.ips) >= 2:
            # Block this fingerprint
            self._blocked_fingerprints[fingerprint] = current_time
            pattern.blocked = True
            pattern.blocked_at = current_time

            logger.warning(
                f"DDoS pattern detected! Fingerprint: {fingerprint[:8]}..., "
                f"IPs: {len(pattern.ips)}, Requests: {pattern.count}, "
                f"Path: {path}"
            )

            return True, "Suspicious request pattern detected and blocked"

        return False, None

    def get_stats(self) -> Dict:
        """Get current protection statistics."""
        return {
            "active_patterns": len(self._patterns),
            "blocked_fingerprints": len(self._blocked_fingerprints),
            "top_patterns": [
                {
                    "fingerprint": fp[:8] + "...",
                    "count": p.count,
                    "unique_ips": len(p.ips),
                    "blocked": p.blocked
                }
                for fp, p in sorted(
                    self._patterns.items(),
                    key=lambda x: x[1].count,
                    reverse=True
                )[:10]
            ]
        }


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for DDoS protection.
    """

    def __init__(
        self,
        app,
        pattern_threshold: int = 5,
        time_window: int = 60,
        block_duration: int = 300,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.protection = DDoSProtection(
            pattern_threshold=pattern_threshold,
            time_window=time_window,
            block_duration=block_duration
        )
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Get request details
        ip = self._get_client_ip(request)
        method = request.method
        user_agent = request.headers.get("user-agent", "")
        content_type = request.headers.get("content-type")
        query_params = str(request.query_params)

        # Read body for POST/PUT/PATCH requests
        body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
            except Exception:
                pass

        # Check request
        is_blocked, reason = self.protection.check_request(
            ip=ip,
            method=method,
            path=path,
            user_agent=user_agent,
            content_type=content_type,
            body=body,
            query_params=query_params
        )

        if is_blocked:
            logger.warning(f"DDoS: Blocked request from {ip} to {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": reason,
                    "error": "too_many_requests",
                    "retry_after": self.protection.block_duration
                },
                headers={
                    "Retry-After": str(self.protection.block_duration),
                    "X-RateLimit-Reset": str(int(time.time()) + self.protection.block_duration)
                }
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, considering proxies."""
        # Check X-Forwarded-For header (from load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


# Singleton instance for stats access
_ddos_protection: Optional[DDoSProtection] = None


def get_ddos_protection() -> Optional[DDoSProtection]:
    """Get the DDoS protection instance for stats."""
    return _ddos_protection


def create_ddos_middleware(
    app,
    pattern_threshold: int = 5,
    time_window: int = 60,
    block_duration: int = 300,
    exclude_paths: Optional[list] = None
) -> DDoSProtectionMiddleware:
    """
    Create DDoS protection middleware.

    Args:
        app: FastAPI application
        pattern_threshold: Number of similar requests before blocking (default: 5)
        time_window: Time window in seconds to count requests (default: 60)
        block_duration: How long to block in seconds (default: 300 = 5 min)
        exclude_paths: Paths to exclude from protection

    Returns:
        DDoSProtectionMiddleware instance
    """
    global _ddos_protection

    middleware = DDoSProtectionMiddleware(
        app,
        pattern_threshold=pattern_threshold,
        time_window=time_window,
        block_duration=block_duration,
        exclude_paths=exclude_paths
    )

    _ddos_protection = middleware.protection

    return middleware

