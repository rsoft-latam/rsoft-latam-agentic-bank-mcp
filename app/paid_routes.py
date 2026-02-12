"""Paid REST endpoints — protected by x402 USDC micropayments.

These endpoints mirror the free MCP tools but are served as standard
HTTP REST routes with x402 payment middleware.  Any agent with a wallet
on Base can pay automatically and get the response.

Free (MCP):     POST /mcp  → consultar_solvencia, bank://tasas_interes
Paid (REST):    GET  /paid/tasas-interes   → 0.001 USDC
                POST /paid/prestamo        → 0.01  USDC
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.backend_client import (
    obtener_tasas_interes,
    solicitar_prestamo,
)

logger = logging.getLogger(__name__)

paid_router = APIRouter(prefix="/paid", tags=["Paid (x402)"])


@paid_router.get("/tasas-interes")
async def paid_tasas_interes() -> dict[str, Any]:
    """Get current interest rates (x402 payment required: 0.001 USDC)."""
    return await obtener_tasas_interes()


@paid_router.post("/prestamo")
async def paid_solicitar_prestamo(body: dict) -> dict[str, Any]:
    """Request a loan (x402 payment required: 0.01 USDC)."""
    agent_id = body.get("agent_id", "")
    monto = body.get("monto", 0)

    if not agent_id:
        return {"error": True, "mensaje": "agent_id es requerido."}
    if monto <= 0:
        return {"error": True, "mensaje": "El monto debe ser mayor a 0."}

    return await solicitar_prestamo(agent_id=agent_id, monto=monto)
