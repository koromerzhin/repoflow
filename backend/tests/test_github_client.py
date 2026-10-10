"""Tests du client HTTP GitHub, sans aucun appel réseau (MockTransport)."""

from __future__ import annotations

import httpx
import pytest

from app.core.errors import NotFoundError, ProviderError
from app.integrations.github.client import GitHubClient, parse_next_link
from app.integrations.github.errors import (
    GitHubAuthError,
    GitHubPermissionError,
    GitHubRateLimitError,
)


def make_client(handler, **kwargs) -> GitHubClient:
    transport = httpx.MockTransport(handler)
    return GitHubClient(
        token="secret-token",
        api_url="https://api.github.com",
        transport=transport,
        **kwargs,
    )


def test_parse_next_link() -> None:
    header = (
        '<https://api.github.com/x?page=2>; rel="next", '
        '<https://api.github.com/x?page=5>; rel="last"'
    )
    assert parse_next_link(header) == "https://api.github.com/x?page=2"
    assert parse_next_link(None) is None
    assert parse_next_link('<https://api.github.com/x?page=1>; rel="prev"') is None


async def test_authentification_en_entete_pas_dans_url() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)
    try:
        await client.get("/user")
    finally:
        await client.aclose()

    assert captured["auth"] == "Bearer secret-token"
    assert "secret-token" not in captured["url"]


async def test_pagination_suit_les_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params.get("page")
        if page == "1":
            return httpx.Response(
                200,
                json=[{"id": 1}, {"id": 2}],
                headers={"Link": '<https://api.github.com/user/repos?page=2>; rel="next"'},
            )
        return httpx.Response(200, json=[{"id": 3}])

    client = make_client(handler)
    try:
        items = await client.get_paginated("/user/repos")
    finally:
        await client.aclose()

    assert [item["id"] for item in items] == [1, 2, 3]


async def test_pagination_bornee_par_max_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"id": 1}],
            headers={"Link": '<https://api.github.com/user/repos?page=2>; rel="next"'},
        )

    client = make_client(handler, max_pages=3)
    try:
        items = await client.get_paginated("/user/repos")
    finally:
        await client.aclose()

    assert len(items) == 3


async def test_items_key_extrait_liste_imbriquee() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"total_count": 2, "check_runs": [{"name": "a"}, {"name": "b"}]}
        )

    client = make_client(handler)
    try:
        items = await client.get_paginated(
            "/repos/o/r/commits/sha/check-runs", items_key="check_runs"
        )
    finally:
        await client.aclose()

    assert len(items) == 2


async def test_erreur_401_auth() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    client = make_client(handler)
    try:
        with pytest.raises(GitHubAuthError):
            await client.get("/user")
    finally:
        await client.aclose()


async def test_erreur_404_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    client = make_client(handler)
    try:
        with pytest.raises(NotFoundError):
            await client.get("/repos/o/r")
    finally:
        await client.aclose()


async def test_erreur_500_provider() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = make_client(handler)
    try:
        with pytest.raises(ProviderError):
            await client.get("/user")
    finally:
        await client.aclose()


async def test_erreur_403_permissions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "Forbidden"})

    client = make_client(handler)
    try:
        with pytest.raises(GitHubPermissionError):
            await client.get("/user")
    finally:
        await client.aclose()


async def test_rate_limit_detecte() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"},
        )

    client = make_client(handler)
    try:
        with pytest.raises(GitHubRateLimitError) as excinfo:
            await client.get("/user")
    finally:
        await client.aclose()

    assert excinfo.value.reset_at == 1700000000


async def test_rate_limit_bloque_page_suivante() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"id": 1}],
            headers={
                "x-ratelimit-remaining": "0",
                "Link": '<https://api.github.com/x?page=2>; rel="next"',
            },
        )

    client = make_client(handler)
    try:
        with pytest.raises(GitHubRateLimitError):
            await client.get_paginated("/user/repos")
    finally:
        await client.aclose()
