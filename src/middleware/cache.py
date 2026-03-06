"""
Caching middleware for API responses.
Caches repeated queries for performance.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional
from collections import OrderedDict
import asyncio


class QueryCache:
    """
    Simple in-memory LRU cache for query results.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries (default 5 minutes)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = asyncio.Lock()

    def _generate_key(self, query: str, document_id: Optional[str] = None) -> str:
        """Generate cache key from query and document ID."""
        key_data = f"{query.lower().strip()}:{document_id or 'all'}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    async def get(self, query: str, document_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result for query.

        Returns:
            Cached result or None if not found/expired
        """
        async with self._lock:
            key = self._generate_key(query, document_id)

            if key not in self.cache:
                return None

            entry = self.cache[key]

            # Check if expired
            if time.time() > entry["expires_at"]:
                del self.cache[key]
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)

            return entry["data"]

    async def set(
        self,
        query: str,
        result: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> None:
        """
        Cache query result.

        Args:
            query: The query string
            result: The result to cache
            document_id: Optional document ID scope
        """
        async with self._lock:
            key = self._generate_key(query, document_id)

            # Remove oldest entries if at capacity
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)

            self.cache[key] = {
                "data": result,
                "expires_at": time.time() + self.ttl_seconds,
                "query": query,
                "document_id": document_id
            }

    async def invalidate(self, document_id: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            document_id: If provided, only invalidate entries for this document.
                        If None, invalidate all entries.

        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            if document_id is None:
                count = len(self.cache)
                self.cache.clear()
                return count

            # Find and remove entries for specific document
            keys_to_remove = [
                key for key, entry in self.cache.items()
                if entry.get("document_id") == document_id
            ]

            for key in keys_to_remove:
                del self.cache[key]

            return len(keys_to_remove)

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            now = time.time()
            active_entries = sum(
                1 for entry in self.cache.values()
                if entry["expires_at"] > now
            )

            return {
                "total_entries": len(self.cache),
                "active_entries": active_entries,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }


# Singleton instance
_query_cache: Optional[QueryCache] = None


def get_query_cache(max_size: int = 100, ttl_seconds: int = 300) -> QueryCache:
    """Get or create query cache singleton."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache(max_size=max_size, ttl_seconds=ttl_seconds)
    return _query_cache

