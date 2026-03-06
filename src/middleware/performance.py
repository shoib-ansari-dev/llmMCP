"""
Performance Optimization Module
Caching, connection pooling, and async optimizations.
"""

import asyncio
from functools import lru_cache
from typing import Optional, Any
import hashlib
import time


class ResponseCache:
    """
    In-memory response cache with TTL.
    Faster than query cache for hot paths.
    """

    def __init__(self, max_size: int = 500, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict = {}
        self._access_times: dict = {}

    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None

        self._access_times[key] = time.time()
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache a value with TTL."""
        # Evict oldest entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest(self.max_size // 4)

        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self.default_ttl)
        }
        self._access_times[key] = time.time()

    def _evict_oldest(self, count: int) -> None:
        """Evict oldest accessed entries."""
        if not self._access_times:
            return

        sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
        for key, _ in sorted_keys[:count]:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_times.clear()


class AsyncBatcher:
    """
    Batch multiple async requests together for efficiency.
    Useful for embedding requests.
    """

    def __init__(self, batch_size: int = 10, max_wait_ms: int = 50):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self._pending: list = []
        self._lock = asyncio.Lock()

    async def add(self, item: Any) -> int:
        """Add item to batch, returns batch index."""
        async with self._lock:
            index = len(self._pending)
            self._pending.append(item)
            return index

    async def get_batch(self) -> list:
        """Get and clear pending batch."""
        async with self._lock:
            batch = self._pending.copy()
            self._pending.clear()
            return batch

    def should_process(self) -> bool:
        """Check if batch should be processed."""
        return len(self._pending) >= self.batch_size


class ConnectionPool:
    """
    Simple connection pool for reusing HTTP connections.
    """

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._semaphore = asyncio.Semaphore(max_connections)

    async def acquire(self):
        """Acquire a connection slot."""
        await self._semaphore.acquire()

    def release(self):
        """Release a connection slot."""
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        self.release()


# =================================
# Performance Decorators
# =================================

def async_cached(ttl_seconds: int = 60, max_size: int = 100):
    """
    Decorator for caching async function results.
    """
    cache = ResponseCache(max_size=max_size, default_ttl=ttl_seconds)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = cache._make_key(func.__name__, *args, **kwargs)

            # Check cache
            cached = cache.get(key)
            if cached is not None:
                return cached

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(key, result)

            return result

        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        return wrapper

    return decorator


def rate_limited(calls_per_second: float = 10):
    """
    Decorator to rate limit function calls.
    """
    min_interval = 1.0 / calls_per_second
    last_call = [0.0]
    lock = asyncio.Lock()

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with lock:
                elapsed = time.time() - last_call[0]
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
                last_call[0] = time.time()

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =================================
# Lazy Loading
# =================================

class LazyLoader:
    """
    Lazy load expensive resources.
    """

    def __init__(self, loader_func):
        self._loader = loader_func
        self._value = None
        self._loaded = False
        self._lock = asyncio.Lock()

    async def get(self):
        """Get the lazily loaded value."""
        if self._loaded:
            return self._value

        async with self._lock:
            if not self._loaded:
                if asyncio.iscoroutinefunction(self._loader):
                    self._value = await self._loader()
                else:
                    self._value = self._loader()
                self._loaded = True

        return self._value

    def reset(self):
        """Reset to trigger reload on next access."""
        self._loaded = False
        self._value = None


# =================================
# Compression
# =================================

import gzip
import json


def compress_response(data: dict) -> bytes:
    """Compress response data with gzip."""
    json_str = json.dumps(data)
    return gzip.compress(json_str.encode())


def decompress_response(data: bytes) -> dict:
    """Decompress gzip response data."""
    json_str = gzip.decompress(data).decode()
    return json.loads(json_str)


# =================================
# Singleton instances
# =================================

_response_cache: Optional[ResponseCache] = None
_connection_pool: Optional[ConnectionPool] = None


def get_response_cache() -> ResponseCache:
    """Get response cache singleton."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache


def get_connection_pool(max_connections: int = 10) -> ConnectionPool:
    """Get connection pool singleton."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool(max_connections)
    return _connection_pool

