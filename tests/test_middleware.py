"""
Tests for middleware components.
"""

import pytest
import asyncio
import time


class TestRateLimiter:
    """Tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_allows_first_request(self):
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=5)
        is_allowed, retry_after = await limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_after_limit(self):
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=2)

        # First two requests should pass
        await limiter.is_allowed("192.168.1.1")
        await limiter.is_allowed("192.168.1.1")

        # Third request should be blocked
        is_allowed, retry_after = await limiter.is_allowed("192.168.1.1")

        assert is_allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_different_ips_independent(self):
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=1)

        # First IP uses its quota
        await limiter.is_allowed("192.168.1.1")
        is_allowed1, _ = await limiter.is_allowed("192.168.1.1")

        # Second IP should still be allowed
        is_allowed2, _ = await limiter.is_allowed("192.168.1.2")

        assert is_allowed1 is False
        assert is_allowed2 is True

    @pytest.mark.asyncio
    async def test_reset_clears_limits(self):
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=1)

        await limiter.is_allowed("192.168.1.1")
        is_allowed, _ = await limiter.is_allowed("192.168.1.1")
        assert is_allowed is False

        limiter.reset("192.168.1.1")

        is_allowed, _ = await limiter.is_allowed("192.168.1.1")
        assert is_allowed is True


class TestQueryCache:
    """Tests for query cache."""

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        from src.middleware.cache import QueryCache

        cache = QueryCache(max_size=10, ttl_seconds=60)
        result = await cache.get("test query")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        from src.middleware.cache import QueryCache

        cache = QueryCache(max_size=10, ttl_seconds=60)

        await cache.set("test query", {"answer": "test answer"})
        result = await cache.get("test query")

        assert result is not None
        assert result["answer"] == "test answer"

    @pytest.mark.asyncio
    async def test_cache_with_document_id(self):
        from src.middleware.cache import QueryCache

        cache = QueryCache(max_size=10, ttl_seconds=60)

        # Same query, different documents
        await cache.set("what is this?", {"answer": "doc1 answer"}, "doc1")
        await cache.set("what is this?", {"answer": "doc2 answer"}, "doc2")

        result1 = await cache.get("what is this?", "doc1")
        result2 = await cache.get("what is this?", "doc2")

        assert result1["answer"] == "doc1 answer"
        assert result2["answer"] == "doc2 answer"

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        from src.middleware.cache import QueryCache

        cache = QueryCache(max_size=10, ttl_seconds=60)

        await cache.set("query1", {"answer": "1"}, "doc1")
        await cache.set("query2", {"answer": "2"}, "doc1")
        await cache.set("query3", {"answer": "3"}, "doc2")

        # Invalidate doc1 entries
        count = await cache.invalidate("doc1")

        assert count == 2
        assert await cache.get("query1", "doc1") is None
        assert await cache.get("query3", "doc2") is not None

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        from src.middleware.cache import QueryCache

        cache = QueryCache(max_size=3, ttl_seconds=60)

        await cache.set("q1", {"a": "1"})
        await cache.set("q2", {"a": "2"})
        await cache.set("q3", {"a": "3"})
        await cache.set("q4", {"a": "4"})  # Should evict q1

        assert await cache.get("q1") is None
        assert await cache.get("q4") is not None


class TestSessionManager:
    """Tests for session manager."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        from src.middleware.session import SessionManager

        manager = SessionManager(session_ttl=60)
        session = await manager.create_session("192.168.1.1")

        assert "session_id" in session
        assert "csrf_token" in session
        assert len(session["session_id"]) > 0
        assert len(session["csrf_token"]) > 0

    @pytest.mark.asyncio
    async def test_validate_csrf_valid(self):
        from src.middleware.session import SessionManager

        manager = SessionManager(session_ttl=60)
        session = await manager.create_session("192.168.1.1")

        is_valid = await manager.validate_csrf(
            session["session_id"],
            session["csrf_token"]
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_csrf_invalid(self):
        from src.middleware.session import SessionManager

        manager = SessionManager(session_ttl=60)
        session = await manager.create_session("192.168.1.1")

        is_valid = await manager.validate_csrf(
            session["session_id"],
            "invalid_token"
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_destroy_session(self):
        from src.middleware.session import SessionManager

        manager = SessionManager(session_ttl=60)
        session = await manager.create_session("192.168.1.1")

        await manager.destroy_session(session["session_id"])

        result = await manager.get_session(session["session_id"])
        assert result is None


class TestMetricsCollector:
    """Tests for metrics collector."""

    @pytest.mark.asyncio
    async def test_record_request(self):
        from src.middleware.logging import MetricsCollector

        collector = MetricsCollector()

        await collector.record_request("/api/test", 200, 50.5)
        await collector.record_request("/api/test", 404, 25.0)

        metrics = await collector.get_metrics()

        assert metrics["requests_total"] == 2
        assert metrics["requests_by_status"]["200"] == 1
        assert metrics["requests_by_status"]["404"] == 1
        assert metrics["errors_total"] == 1

    @pytest.mark.asyncio
    async def test_error_rate_calculation(self):
        from src.middleware.logging import MetricsCollector

        collector = MetricsCollector()

        await collector.record_request("/api/test", 200, 10)
        await collector.record_request("/api/test", 200, 10)
        await collector.record_request("/api/test", 500, 10)
        await collector.record_request("/api/test", 400, 10)

        metrics = await collector.get_metrics()

        assert metrics["error_rate"] == 0.5  # 2 errors out of 4

