"""Middleware modules for API."""

from .rate_limiter import RateLimiter, RateLimitMiddleware, get_rate_limiter
from .cache import QueryCache, get_query_cache
from .session import SessionManager, CSRFMiddleware, get_session_manager
from .logging import (
    LoggingMiddleware,
    MetricsCollector,
    RequestLogger,
    setup_logging,
    get_metrics_collector
)
from .performance import (
    ResponseCache,
    AsyncBatcher,
    ConnectionPool,
    LazyLoader,
    async_cached,
    rate_limited,
    get_response_cache,
    get_connection_pool,
    compress_response,
    decompress_response
)
from .ddos_protection import (
    DDoSProtection,
    DDoSProtectionMiddleware,
    create_ddos_middleware,
    get_ddos_protection
)

__all__ = [
    "RateLimiter",
    "RateLimitMiddleware",
    "get_rate_limiter",
    "QueryCache",
    "get_query_cache",
    "SessionManager",
    "CSRFMiddleware",
    "get_session_manager",
    "LoggingMiddleware",
    "MetricsCollector",
    "RequestLogger",
    "setup_logging",
    "get_metrics_collector",
    "ResponseCache",
    "AsyncBatcher",
    "ConnectionPool",
    "LazyLoader",
    "async_cached",
    "rate_limited",
    "get_response_cache",
    "get_connection_pool",
    "compress_response",
    "decompress_response",
    "DDoSProtection",
    "DDoSProtectionMiddleware",
    "create_ddos_middleware",
    "get_ddos_protection",
]

