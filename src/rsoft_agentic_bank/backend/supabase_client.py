"""Supabase integration layer for RSoft Agentic Bank."""

from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from rsoft_agentic_bank.config import settings

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


async def obtener_historial_crediticio(agent_id: str) -> dict[str, Any]:
    """Fetch the full credit history for a given agent from Supabase.

    Returns a dict with keys: agent_id, score, historial (list of records),
    deuda_actual, and estado.
    """
    client = _get_client()
    response = (
        client.table("historial_crediticio")
        .select("*")
        .eq("agent_id", agent_id)
        .execute()
    )

    if not response.data:
        return {
            "agent_id": agent_id,
            "score": 0,
            "historial": [],
            "deuda_actual": 0.0,
            "estado": "sin_registro",
        }

    registros = response.data
    ultimo = registros[-1]

    return {
        "agent_id": agent_id,
        "score": ultimo.get("score", 0),
        "historial": registros,
        "deuda_actual": ultimo.get("deuda_actual", 0.0),
        "estado": ultimo.get("estado", "activo"),
    }


async def obtener_tasas_interes() -> dict[str, Any]:
    """Return the current interest-rate schedule from Supabase."""
    client = _get_client()
    response = (
        client.table("tasas_interes")
        .select("*")
        .eq("activo", True)
        .order("created_at", desc=True)
        .execute()
    )

    if not response.data:
        return {
            "tasas": [],
            "mensaje": "No hay tasas configuradas actualmente.",
        }

    return {
        "tasas": response.data,
        "moneda": "USDC",
        "red": "Base",
        "ultima_actualizacion": response.data[0].get("created_at"),
    }


async def registrar_prestamo(
    agent_id: str,
    monto: float,
    tx_hash: str,
    estado: str = "aprobado",
) -> dict[str, Any]:
    """Insert a new loan record into the prestamos table."""
    client = _get_client()
    response = (
        client.table("prestamos")
        .insert(
            {
                "agent_id": agent_id,
                "monto": monto,
                "tx_hash": tx_hash,
                "estado": estado,
            }
        )
        .execute()
    )
    return response.data[0] if response.data else {}
