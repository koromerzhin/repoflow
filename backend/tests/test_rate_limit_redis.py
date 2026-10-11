"""Tests du limiteur de débit distribué (Redis, repli mémoire)."""

from __future__ import annotations

import logging
from typing import Any

import pytest

from app.core.security import RateLimiter, RedisRateLimiter, build_rate_limiter


class FakeRedis:
    """Client Redis en mémoire implémentant le protocole utilisé."""

    def __init__(self, *, fail: bool = False) -> None:
        self._data: dict[str, int] = {}
        self._ttl: dict[str, int] = {}
        self.fail = fail

    async def incr(self, key: str) -> int:
        if self.fail:
            raise ConnectionError("redis down")
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]

    async def expire(self, key: str, seconds: int) -> None:
        if self.fail:
            raise ConnectionError("redis down")
        self._ttl[key] = seconds

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError("redis down")
        value = self._data.get(key)
        return str(value) if value is not None else None


def _limiter(fake: FakeRedis, *, requests: int = 2) -> RedisRateLimiter:
    async def factory() -> Any:
        return fake

    return RedisRateLimiter(requests=requests, window_seconds=60, client_factory=factory)


async def test_redis_compte_les_requetes_par_client() -> None:
    fake = FakeRedis()
    limiter = _limiter(fake)

    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is False
    assert await limiter.remaining("client-a") == 0
    assert await limiter.allow("client-b") is True
    assert fake._ttl.get("repoflow:ratelimit:client-a") == 60


async def test_redis_panne_repli_memoire(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake = FakeRedis(fail=True)
    limiter = _limiter(fake, requests=2)

    with caplog.at_level(logging.WARNING, logger="app.core.security"):
        assert await limiter.allow("client-a") is True
        assert await limiter.allow("client-a") is True
        # Repli mémoire : le seuil est appliqué localement.
        assert await limiter.allow("client-a") is False
        assert await limiter.remaining("client-a") == 0

    assert any("repli" in record.message for record in caplog.records)


async def test_redis_panne_partielle_repli_coherent() -> None:
    fake = FakeRedis()
    limiter = _limiter(fake, requests=2)

    assert await limiter.allow("client-a") is True
    fake.fail = True

    # La panne bascule sur mémoire : le compteur local repart de zéro
    # et applique le même seuil.
    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is False


def test_build_rate_limiter_choisit_le_backend() -> None:
    assert isinstance(
        build_rate_limiter(backend="memory", requests=2, window_seconds=60),
        RateLimiter,
    )
    assert isinstance(
        build_rate_limiter(backend="redis", requests=2, window_seconds=60),
        RedisRateLimiter,
    )
