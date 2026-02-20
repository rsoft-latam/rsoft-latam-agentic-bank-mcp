"""Paid REST endpoints — protected by x402 USDC micropayments.

These endpoints mirror the free MCP tools but are served as standard
HTTP REST routes with x402 payment middleware.  Any agent with a wallet
on Base can pay automatically and get the response.

Free (MCP):     POST /mcp  → get_creditworthiness, bank://interest_rates
Paid (REST):    GET  /paid/interest-rates   → 0.001 USDC
                POST /paid/loans            → 0.01  USDC
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.backend_client import (
    get_interest_rates,
    request_loan,
)

logger = logging.getLogger(__name__)

paid_router = APIRouter(prefix="/paid", tags=["Paid (x402)"])


@paid_router.get("/interest-rates")
async def paid_interest_rates() -> dict[str, Any]:
    """Get current interest rates (x402 payment required: 0.001 USDC)."""
    return await get_interest_rates()


@paid_router.post("/loans")
async def paid_request_loan(body: dict) -> dict[str, Any]:
    """Request a loan (x402 payment required: 0.01 USDC)."""
    agent_id = body.get("agent_id", "")
    amount = body.get("amount", 0)

    if not agent_id:
        return {"error": True, "message": "agent_id is required."}
    if amount <= 0:
        return {"error": True, "message": "Amount must be greater than 0."}

    return await request_loan(agent_id=agent_id, amount=amount)
