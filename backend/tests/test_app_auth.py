"""Tests de l'authentification GitHub App (JWT → jeton d'installation)."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import httpx
import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.errors import NotConfiguredError
from app.integrations.github.app_auth import InstallationTokenProvider, load_private_key
from app.integrations.github.errors import GitHubAuthError, GitHubPermissionError

_APP_ID = "123456"
_INSTALLATION_ID = 789


def _generate_private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


_PRIVATE_KEY_PEM = _generate_private_key_pem()


def make_provider(handler, **kwargs) -> InstallationTokenProvider:
    transport = httpx.MockTransport(handler)
    return InstallationTokenProvider(
        _APP_ID,
        kwargs.pop("private_key", _PRIVATE_KEY_PEM),
        kwargs.pop("installation_id", _INSTALLATION_ID),
        transport=transport,
        **kwargs,
    )


def test_load_private_key_accepte_pem() -> None:
    assert load_private_key(_PRIVATE_KEY_PEM) == _PRIVATE_KEY_PEM.strip()


def test_load_private_key_accepte_pem_echappe() -> None:
    escaped = _PRIVATE_KEY_PEM.replace("\n", "\\n")
    assert load_private_key(escaped) == _PRIVATE_KEY_PEM.strip()


def test_load_private_key_accepte_base64() -> None:
    encoded = base64.b64encode(_PRIVATE_KEY_PEM.encode("utf-8")).decode("ascii")
    assert load_private_key(encoded) == _PRIVATE_KEY_PEM.strip()


def test_load_private_key_invalide_leve_erreur() -> None:
    with pytest.raises(NotConfiguredError):
        load_private_key("pas-une-cle")


async def test_echange_jwt_contre_jeton_installation() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization", "")
        captured["url"] = str(request.url)
        return httpx.Response(
            201,
            json={
                "token": "ghs_installation_token",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            },
        )

    provider = make_provider(handler)
    try:
        token = await provider.get_token()
    finally:
        await provider.aclose()

    assert token == "ghs_installation_token"
    assert captured["url"].endswith("/app/installations/789/access_tokens")
    assertion = captured["auth"].removeprefix("Bearer ")
    claims = pyjwt.decode(
        assertion,
        options={"verify_signature": False},
        algorithms=["RS256"],
    )
    assert claims["iss"] == _APP_ID


async def test_jeton_mis_en_cache_sans_nouvelle_requete() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(
            201,
            json={
                "token": "ghs_installation_token",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            },
        )

    provider = make_provider(handler)
    try:
        first = await provider.get_token()
        second = await provider.get_token()
    finally:
        await provider.aclose()

    assert first == second == "ghs_installation_token"
    assert len(calls) == 1


async def test_renouvellement_proche_expiration() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(
            201,
            json={
                "token": f"ghs_token_{len(calls)}",
                # Expire dans 100 s : sous la marge de renouvellement (300 s).
                "expires_at": (datetime.now(UTC) + timedelta(seconds=100)).isoformat(),
            },
        )

    provider = make_provider(handler)
    try:
        first = await provider.get_token()
        second = await provider.get_token()
    finally:
        await provider.aclose()

    assert first == "ghs_token_1"
    assert second == "ghs_token_2"
    assert len(calls) == 2


async def test_expiration_absolue_utilise_delai_par_defaut() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"token": "ghs_token", "expires_at": "illisible"})

    provider = make_provider(handler)
    try:
        token = await provider.get_token()
        assert token == "ghs_token"
    finally:
        await provider.aclose()


async def test_jwt_invalide_leve_erreur_auth() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    provider = make_provider(handler)
    try:
        with pytest.raises(GitHubAuthError):
            await provider.get_token()
    finally:
        await provider.aclose()


async def test_installation_inconnue_leve_erreur_auth() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    provider = make_provider(handler)
    try:
        with pytest.raises(GitHubAuthError):
            await provider.get_token()
    finally:
        await provider.aclose()


async def test_application_non_installee_leve_erreur_permission() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "Forbidden"})

    provider = make_provider(handler)
    try:
        with pytest.raises(GitHubPermissionError):
            await provider.get_token()
    finally:
        await provider.aclose()


async def test_jwt_signe_avec_la_cle_fournie() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(
            201,
            json={
                "token": "ghs_token",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            },
        )

    provider = make_provider(handler)
    try:
        await provider.get_token()
    finally:
        await provider.aclose()

    assertion = captured["auth"].removeprefix("Bearer ")
    header = pyjwt.get_unverified_header(assertion)
    assert header["alg"] == "RS256"
