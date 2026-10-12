"""Tests du client HTTP GitHub, sans aucun appel réseau (MockTransport)."""

from __future__ import annotations

import httpx
import pytest

from app.core.errors import NotFoundError, ProviderError
from app.integrations.github import ratelimit
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


async def test_requete_conditionnelle_etag_304_renvoie_cache() -> None:
    requests: list[httpx.Request] = []
    body = [{"id": 1}]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "if-none-match" in request.headers:
            return httpx.Response(304)
        return httpx.Response(200, json=body, headers={"ETag": 'W/"abc123"'})

    client = make_client(handler)
    try:
        first = await client.get("/user/repos")
        second = await client.get("/user/repos")
    finally:
        await client.aclose()

    assert first == body
    assert second == body
    assert len(requests) == 2
    assert requests[1].headers["if-none-match"] == 'W/"abc123"'


async def test_etag_invalide_200_met_a_jour_cache() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(200, json={"v": 1}, headers={"ETag": 'W/"a"'})
        if "if-none-match" in request.headers:
            return httpx.Response(200, json={"v": 2}, headers={"ETag": 'W/"b"'})
        return httpx.Response(200, json={"v": 2})

    client = make_client(handler)
    try:
        first = await client.get("/user")
        second = await client.get("/user")
    finally:
        await client.aclose()

    assert first == {"v": 1}
    assert second == {"v": 2}


async def test_pagination_304_suit_le_lien_en_cache() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = request.url.params.get("page")
        if "if-none-match" in request.headers:
            return httpx.Response(304)
        if page == "1":
            return httpx.Response(
                200,
                json=[{"id": 1}],
                headers={
                    "ETag": 'W/"p1"',
                    "Link": '<https://api.github.com/x?page=2>; rel="next"',
                },
            )
        return httpx.Response(200, json=[{"id": 2}], headers={"ETag": 'W/"p2"'})

    client = make_client(handler)
    try:
        first = await client.get_paginated("/x")
        second = await client.get_paginated("/x")
    finally:
        await client.aclose()

    assert [item["id"] for item in first] == [1, 2]
    assert [item["id"] for item in second] == [1, 2]
    page1_second = [r for r in requests[3:] if r.url.params.get("page") == "1"]
    assert all("if-none-match" in r.headers for r in page1_second)


async def test_limite_secondaire_retry_after_reessaie_une_fois() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(
                403,
                json={"message": "secondary rate limit"},
                headers={"Retry-After": "0"},
            )
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)
    try:
        payload = await client.get("/user")
    finally:
        await client.aclose()

    assert payload == {"ok": True}
    assert len(calls) == 2


async def test_limite_secondaire_plafonnee_et_erreur_si_persistante() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(
            429,
            json={"message": "secondary rate limit"},
            headers={"Retry-After": "9999"},
        )

    client = make_client(handler, max_retry_after=0.01)
    try:
        with pytest.raises(GitHubRateLimitError):
            await client.get("/user")
    finally:
        await client.aclose()

    assert len(calls) == 2


async def test_rate_limit_primaire_sans_retry_after_n_eessaie_pas() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"},
        )

    client = make_client(handler)
    try:
        with pytest.raises(GitHubRateLimitError):
            await client.get("/user")
    finally:
        await client.aclose()

    assert len(calls) == 1


async def test_quota_enregistre_apres_reponse() -> None:
    ratelimit.reset()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True},
            headers={
                "x-ratelimit-remaining": "4998",
                "x-ratelimit-limit": "5000",
                "x-ratelimit-reset": "1700000000",
            },
        )

    client = make_client(handler)
    try:
        await client.get("/user")
        snapshot = ratelimit.snapshot()
    finally:
        await client.aclose()
        ratelimit.reset()

    assert snapshot == {
        "resource": "core",
        "remaining": 4998,
        "limit": 5000,
        "reset_at": 1700000000,
    }


async def test_quota_non_renseigne_sans_entetes() -> None:
    ratelimit.reset()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)
    try:
        await client.get("/user")
        snapshot = ratelimit.snapshot()
    finally:
        await client.aclose()

    assert snapshot is None


async def test_token_provider_autorise_chaque_requete() -> None:
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.headers.get("authorization", ""))
        return httpx.Response(200, json={"ok": True})

    tokens = iter(["ghs_token_1", "ghs_token_2"])

    async def provider() -> str:
        return next(tokens)

    client = GitHubClient(
        None,
        "https://api.github.com",
        transport=httpx.MockTransport(handler),
        token_provider=provider,
    )
    try:
        await client.get("/user")
        await client.get("/user")
    finally:
        await client.aclose()

    assert captured == ["Bearer ghs_token_1", "Bearer ghs_token_2"]
