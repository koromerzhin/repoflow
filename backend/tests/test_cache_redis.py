"""Tests du backend Redis du cache (client factice, repli mémoire)."""

from __future__ import annotations

import logging

import pytest
from pydantic import BaseModel

from app.core import cache
from app.core.config import Settings


class FakeRedis:
    """Client Redis en mémoire implémentant le protocole utilisé."""

    def __init__(self, *, fail: bool = False) -> None:
        self._data: dict[str, str] = {}
        self.fail = fail

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError("redis down")
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if self.fail:
            raise ConnectionError("redis down")
        self._data[key] = value

    async def aclose(self) -> None:
        pass


@pytest.fixture
def redis_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    cache.clear()
    cache.use_redis_client(None)
    monkeypatch.setattr(cache, "get_settings", lambda: Settings(cache_backend="redis"))
    yield
    cache.clear()
    cache.use_redis_client(None)


async def test_redis_stocke_et_reutilise(redis_settings: None) -> None:
    fake = FakeRedis()
    cache.use_redis_client(fake)
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    first = await cache.get_or_load(("k",), 60, factory)
    second = await cache.get_or_load(("k",), 60, factory)

    assert first == second == 1
    assert calls["n"] == 1
    assert len(fake._data) == 1


async def test_redis_refresh_force_rechargement(redis_settings: None) -> None:
    fake = FakeRedis()
    cache.use_redis_client(fake)
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    await cache.get_or_load(("k",), 60, factory)
    refreshed = await cache.get_or_load(("k",), 60, factory, refresh=True)

    assert refreshed == 2
    assert calls["n"] == 2
    assert len(fake._data) == 1


async def test_redis_ttl_zero_bypass(redis_settings: None) -> None:
    fake = FakeRedis()
    cache.use_redis_client(fake)
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    await cache.get_or_load(("k",), 0, factory)
    await cache.get_or_load(("k",), 0, factory)

    assert calls["n"] == 2
    assert fake._data == {}


async def test_redis_panne_lecture_repli_memoire(
    redis_settings: None, caplog: pytest.LogCaptureFixture
) -> None:
    fake = FakeRedis(fail=True)
    cache.use_redis_client(fake)
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    with caplog.at_level(logging.WARNING, logger="app.core.cache"):
        first = await cache.get_or_load(("k",), 60, factory)
        second = await cache.get_or_load(("k",), 60, factory)

    assert first == second == 1
    assert calls["n"] == 1
    assert any("repli" in record.message for record in caplog.records)


async def test_redis_ecriture_en_echec_repli_memoire(
    redis_settings: None, caplog: pytest.LogCaptureFixture
) -> None:
    class WriteFailRedis(FakeRedis):
        async def set(self, key: str, value: str, ex: int | None = None) -> None:
            raise ConnectionError("redis down")

    cache.use_redis_client(WriteFailRedis())
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    with caplog.at_level(logging.WARNING, logger="app.core.cache"):
        first = await cache.get_or_load(("k",), 60, factory)
        second = await cache.get_or_load(("k",), 60, factory)

    assert first == second == 1
    assert calls["n"] == 1
    assert any("repli" in record.message for record in caplog.records)


async def test_redis_nouvelle_tentative_apres_delai(
    redis_settings: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cache, "_retry_delay_seconds", 0.0)
    fake = FakeRedis(fail=True)
    cache.use_redis_client(fake)
    calls = {"n": 0}

    async def factory() -> int:
        calls["n"] += 1
        return calls["n"]

    await cache.get_or_load(("k",), 60, factory)
    cache._entries.clear()
    fake.fail = False
    value = await cache.get_or_load(("k",), 60, factory)

    assert value == 2
    assert calls["n"] == 2
    assert len(fake._data) == 1


async def test_redis_codec_round_trip(redis_settings: None) -> None:
    class Record(BaseModel):
        name: str
        value: int

    fake = FakeRedis()
    cache.use_redis_client(fake)
    codec = cache.default_codec()
    records = [Record(name="a", value=1), Record(name="b", value=2)]

    async def factory() -> list[Record]:
        return records

    first: list[Record] = await cache.get_or_load(("k",), 60, factory, codec=codec)
    second: list[Record] = await cache.get_or_load(("k",), 60, factory, codec=codec)

    assert first == records
    assert second == records
    assert all(isinstance(item, Record) for item in second)


async def test_integration_redis_reel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cache,
        "get_settings",
        lambda: Settings(cache_backend="redis", cache_redis_url="redis://localhost:6379/0"),
    )
    try:
        client = await cache._ensure_client()
        await client.ping()
    except Exception:
        pytest.skip("Redis réel injoignable")
    cache.clear()
    cache.use_redis_client(None)
    try:
        calls = {"n": 0}

        async def factory() -> dict[str, int]:
            calls["n"] += 1
            return {"v": calls["n"]}

        first = await cache.get_or_load(("it",), 60, factory)
        second = await cache.get_or_load(("it",), 60, factory)

        assert first == second == {"v": 1}
    finally:
        cache.clear()
        cache.use_redis_client(None)
