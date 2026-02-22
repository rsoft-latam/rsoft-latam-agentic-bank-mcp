"""Free REST endpoints — no authentication or payment required.

These endpoints mirror the MCP tools as standard HTTP REST routes,
designed for agents that cannot use MCP natively (e.g. OpenClaw/Telegram).

Free (MCP):     POST /mcp  → get_creditworthiness, bank://interest_rates
Paid (REST):    GET  /paid/interest-rates   → 0.001 USDC
                POST /paid/loans            → 0.01  USDC
Free (REST):    GET  /api/interest-rates    → no payment
                GET  /api/creditworthiness  → no payment
                POST /api/loans             → no payment
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.backend_client import (
    get_creditworthiness,
    get_interest_rates,
    request_loan,
)

logger = logging.getLogger(__name__)

free_router = APIRouter(prefix="/api", tags=["Free API"])


@free_router.get("/interest-rates")
async def free_interest_rates() -> dict[str, Any]:
    """Get current interest rates (free, no payment required)."""
    try:
        return await get_interest_rates()
    except Exception:
        logger.exception("Error fetching interest rates")
        return {"error": True, "message": "Could not fetch interest rates."}


@free_router.get("/creditworthiness/{agent_id}")
async def free_creditworthiness(agent_id: str) -> dict[str, Any]:
    """Get creditworthiness for an agent (free, no payment required)."""
    if not agent_id:
        return {"error": True, "message": "agent_id is required."}
    try:
        return await get_creditworthiness(agent_id)
    except Exception:
        logger.exception("Error fetching creditworthiness for %s", agent_id)
        return {"error": True, "message": "Could not fetch the agent's creditworthiness.", "agent_id": agent_id}


@free_router.post("/loans")
async def free_request_loan(body: dict) -> dict[str, Any]:
    """Request a loan (free, no payment required)."""
    agent_id = body.get("agent_id", "")
    amount = body.get("amount", 0)

    if not agent_id:
        return {"error": True, "message": "agent_id is required."}
    if amount <= 0:
        return {"error": True, "message": "Amount must be greater than 0."}

    try:
        return await request_loan(agent_id=agent_id, amount=amount)
    except Exception:
        logger.exception("Error requesting loan for %s", agent_id)
        return {"error": True, "message": "Could not process the loan request.", "agent_id": agent_id}
