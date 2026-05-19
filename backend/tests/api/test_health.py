"""Tests for ``GET /api/health`` (API_CONTRACT.md §6.1)."""

from __future__ import annotations

import pytest


async def test_health_ok_with_simulator(client, monkeypatch):
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "db": "ok", "market": "simulator"}


async def test_health_market_is_massive_when_key_set(client, monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "fake-key")
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["market"] == "massive"


async def test_health_market_empty_key_treated_as_simulator(client, monkeypatch):
    monkeypatch.setenv("MASSIVE_API_KEY", "   ")
    response = await client.get("/api/health")
    assert response.json()["market"] == "simulator"
