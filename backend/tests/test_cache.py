"""Tests du cache TTL mémoire."""

from __future__ import annotations

import asyncio

import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def _clean_cache() -> None:
    cache.clear()


async def test_valeur_mise_en_cache() -> None:
    appels = {"n": 0}

    async def factory() -> str:
        appels["n"] += 1
        return "valeur"

    first = await cache.get_or_load(("k",), 60, factory)
    second = await cache.get_or_load(("k",), 60, factory)

    assert first == second == "valeur"
    assert appels["n"] == 1


async def test_refresh_force_le_rechargement() -> None:
    appels = {"n": 0}

    async def factory() -> int:
        appels["n"] += 1
        return appels["n"]

    await cache.get_or_load(("k",), 60, factory)
    rafraichi = await cache.get_or_load(("k",), 60, factory, refresh=True)

    assert rafraichi == 2
    assert appels["n"] == 2


async def test_ttl_zero_desactive_le_cache() -> None:
    appels = {"n": 0}

    async def factory() -> int:
        appels["n"] += 1
        return appels["n"]

    a = await cache.get_or_load(("k",), 0, factory)
    b = await cache.get_or_load(("k",), 0, factory)

    assert (a, b) == (1, 2)
    assert appels["n"] == 2


async def test_cles_distinctes() -> None:
    async def factory_a() -> str:
        return "a"

    async def factory_b() -> str:
        return "b"

    assert await cache.get_or_load(("a",), 60, factory_a) == "a"
    assert await cache.get_or_load(("b",), 60, factory_b) == "b"
    assert cache.size() == 2


def test_clear_vide_le_cache() -> None:
    cache._entries[("x",)] = (float("inf"), 1)
    cache.clear()
    assert cache.size() == 0


async def test_chargements_concurrents_coalesces() -> None:
    appels = {"n": 0}

    async def factory() -> int:
        appels["n"] += 1
        await asyncio.sleep(0.01)
        return appels["n"]

    resultats = await asyncio.gather(*(cache.get_or_load(("k",), 60, factory) for _ in range(5)))

    assert resultats == [1, 1, 1, 1, 1]
    assert appels["n"] == 1


async def test_concurrent_refresh_et_lecture_partagent_le_chargement() -> None:
    appels = {"n": 0}

    async def factory() -> int:
        appels["n"] += 1
        await asyncio.sleep(0.01)
        return appels["n"]

    await cache.get_or_load(("k",), 60, factory)
    rafraichi, lecture = await asyncio.gather(
        cache.get_or_load(("k",), 60, factory, refresh=True),
        cache.get_or_load(("k",), 60, factory),
    )

    assert rafraichi == 2
    assert lecture == 2
    assert appels["n"] == 2
