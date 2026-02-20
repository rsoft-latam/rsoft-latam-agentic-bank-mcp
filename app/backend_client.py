"""HTTP client to communicate with the RSoft Agentic Bank backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=get_settings().backend_url,
            timeout=120.0,
        )
    return _client


async def get_creditworthiness(agent_id: str) -> dict[str, Any]:
    """Fetch credit history for a given agent from the backend."""
    client = _get_client()
    response = await client.get(f"/agents/{agent_id}/creditworthiness")
    response.raise_for_status()
    return response.json()


async def request_loan(agent_id: str, amount: float) -> dict[str, Any]:
    """Request a loan through the backend (risk evaluation + blockchain transfer)."""
    client = _get_client()
    response = await client.post(
        "/loans",
        json={"agent_id": agent_id, "amount": amount},
    )
    response.raise_for_status()
    return response.json()


async def get_interest_rates() -> dict[str, Any]:
    """Fetch current interest rates from the backend."""
    client = _get_client()
    response = await client.get("/interest-rates")
    response.raise_for_status()
    return response.json()
