"""Tests des routes d'automatisation et de l'arrêt d'urgence."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_statut_par_defaut(client: TestClient) -> None:
    response = client.get("/api/v1/automation/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["kill_switch_engaged"] is False
    assert payload["global_auto_merge_enabled"] is False
    assert payload["worker_enabled"] is False


def test_arreter_urgence_allume_et_eteint(client: TestClient) -> None:
    engaged = client.post("/api/v1/automation/kill-switch", json={"engaged": True})
    assert engaged.status_code == 200
    assert engaged.json()["kill_switch_engaged"] is True

    assert client.get("/api/v1/automation/status").json()["kill_switch_engaged"] is True

    disengaged = client.post("/api/v1/automation/kill-switch", json={"engaged": False})
    assert disengaged.status_code == 200
    assert disengaged.json()["kill_switch_engaged"] is False
