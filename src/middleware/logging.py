"""
Logging and Monitoring Module.
Provides structured logging and request monitoring.
"""

import logging
import time
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio


class StructuredFormatter(logging.Formatter):
    """
    JSON structured log formatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class RequestLogger:
    """
    Request/Response logger for API monitoring.
    """

    def __init__(self, logger_name: str = "api"):
        self.logger = logging.getLogger(logger_name)

    def log_request(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        client_ip: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log API request details."""
        log_data = {
            "type": "request",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
        }

        if extra:
            log_data.update(extra)

        # Determine log level based on status code
        if response.status_code >= 500:
            self.logger.error("Request failed", extra={"extra": log_data})
        elif response.status_code >= 400:
            self.logger.warning("Request error", extra={"extra": log_data})
        else:
            self.logger.info("Request completed", extra={"extra": log_data})


class MetricsCollector:
    """
    Simple metrics collector for monitoring.
    """

    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_path": {},
            "total_duration_ms": 0,
            "errors_total": 0,
            "start_time": time.time()
        }
        self._lock = asyncio.Lock()

    async def record_request(
        self,
        path: str,
        status_code: int,
        duration_ms: float
    ):
        """Record request metrics."""
        async with self._lock:
            self.metrics["requests_total"] += 1
            self.metrics["total_duration_ms"] += duration_ms

            # By status code
            status_key = str(status_code)
            self.metrics["requests_by_status"][status_key] = \
                self.metrics["requests_by_status"].get(status_key, 0) + 1

            # By path (simplified)
            path_key = path.split("/")[1] if "/" in path else path
            self.metrics["requests_by_path"][path_key] = \
                self.metrics["requests_by_path"].get(path_key, 0) + 1

            # Track errors
            if status_code >= 400:
                self.metrics["errors_total"] += 1

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        async with self._lock:
            uptime = time.time() - self.metrics["start_time"]
            avg_duration = (
                self.metrics["total_duration_ms"] / self.metrics["requests_total"]
                if self.metrics["requests_total"] > 0 else 0
            )

            return {
                **self.metrics,
                "uptime_seconds": round(uptime, 2),
                "avg_duration_ms": round(avg_duration, 2),
                "error_rate": (
                    self.metrics["errors_total"] / self.metrics["requests_total"]
                    if self.metrics["requests_total"] > 0 else 0
                )
            }


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging and monitoring requests.
    """

    # Paths to exclude from logging
    EXCLUDE_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}

    def __init__(
        self,
        app,
        logger: Optional[RequestLogger] = None,
        metrics: Optional[MetricsCollector] = None
    ):
        super().__init__(app)
        self.request_logger = logger or RequestLogger()
        self.metrics = metrics or MetricsCollector()

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        client_ip = self.get_client_ip(request)

        # Record metrics
        await self.metrics.record_request(
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )

        # Log request (skip excluded paths)
        if request.url.path not in self.EXCLUDE_PATHS:
            self.request_logger.log_request(
                request=request,
                response=response,
                duration_ms=duration_ms,
                client_ip=client_ip
            )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


def setup_logging(level: str = "INFO", json_format: bool = False):
    """
    Setup application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON structured logging
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    root_logger.addHandler(handler)

    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


# Singleton instances
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

