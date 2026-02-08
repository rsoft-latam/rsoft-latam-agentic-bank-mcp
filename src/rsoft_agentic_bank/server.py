"""RSoft Agentic Bank — MCP Server.

Exposes banking tools (solvency checks, loan requests) and resources
(interest rates) to LLM agents via the Model Context Protocol.

Supports both STDIO (local/testing) and HTTP+SSE (AWS Lambda / production)
transports.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rsoft_agentic_bank.backend.blockchain import BlockchainError, ejecutar_transferencia_prestamo
from rsoft_agentic_bank.backend.langgraph_flow import evaluar_solicitud_prestamo
from rsoft_agentic_bank.backend.supabase_client import (
    obtener_historial_crediticio,
    obtener_tasas_interes,
    registrar_prestamo,
)
from rsoft_agentic_bank.config import settings

logger = logging.getLogger(__name__)

# ── MCP Server instance ─────────────────────────────────────────────────────

mcp = FastMCP(
    "RSoft_Agentic_Bank",
    instructions=(
        "Servidor bancario inteligente de RSoft Latam. "
        "Permite consultar solvencia crediticia de agentes, solicitar préstamos "
        "que se evalúan con LangGraph y se ejecutan en la red Base (L2), "
        "y consultar las tasas de interés vigentes."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def consultar_solvencia(agent_id: str) -> dict[str, Any]:
    """Consulta la solvencia y el historial crediticio de un agente.

    Usa esta herramienta cuando necesites:
    - Verificar si un agente tiene buen historial crediticio.
    - Obtener el score crediticio actual de un agente.
    - Conocer la deuda vigente de un agente antes de aprobar una operación.
    - Evaluar el riesgo de un agente previo a una solicitud de préstamo.

    Args:
        agent_id: Identificador único del agente en el sistema bancario.
                  Ejemplo: "agent_0x1a2b3c".

    Returns:
        Diccionario con: agent_id, score (0-850), historial (lista de registros),
        deuda_actual (float en USDC) y estado ("activo" | "moroso" | "sin_registro").
    """
    try:
        resultado = await obtener_historial_crediticio(agent_id)
        return resultado
    except Exception as exc:
        logger.exception("Error al consultar solvencia para %s", agent_id)
        return {
            "error": True,
            "mensaje": f"No se pudo consultar la solvencia: {exc}",
            "agent_id": agent_id,
        }


@mcp.tool()
async def solicitar_prestamo(monto: float, agent_id: str) -> dict[str, Any]:
    """Solicita un préstamo que se evalúa con IA y, si se aprueba, ejecuta la
    transferencia de USDC en la red Base (L2).

    Usa esta herramienta cuando:
    - Un agente necesita financiamiento en USDC.
    - Se requiere ejecutar el flujo completo: evaluación de riesgo → aprobación →
      transferencia on-chain.
    - El agente ya fue verificado con `consultar_solvencia` y desea proceder.

    El flujo interno es:
    1. Obtiene el historial crediticio del agente desde Supabase.
    2. Ejecuta el grafo de evaluación de riesgo (LangGraph).
    3. Si se aprueba, dispara la transferencia de USDC en Base Network.
    4. Registra el préstamo en la base de datos.

    Args:
        monto: Monto del préstamo solicitado en USDC. Debe ser > 0.
               Ejemplo: 5000.00
        agent_id: Identificador único del agente solicitante.
                  Ejemplo: "agent_0x1a2b3c".

    Returns:
        Diccionario con el resultado de la solicitud:
        - Si aprobado: incluye tx_hash, block_number, monto, estado "aprobado".
        - Si rechazado: incluye motivo del rechazo y estado "rechazado".
        - Si error: incluye detalle del error.
    """
    # ── Validación básica ────────────────────────────────────────────────
    if monto <= 0:
        return {
            "error": True,
            "mensaje": "El monto debe ser mayor a 0.",
            "agent_id": agent_id,
        }

    # ── 1. Obtener historial crediticio ──────────────────────────────────
    try:
        historial = await obtener_historial_crediticio(agent_id)
    except Exception as exc:
        logger.exception("Error obteniendo historial para %s", agent_id)
        return {
            "error": True,
            "mensaje": f"No se pudo obtener el historial crediticio: {exc}",
            "agent_id": agent_id,
        }

    if historial.get("estado") == "sin_registro":
        return {
            "error": True,
            "mensaje": "El agente no tiene historial crediticio registrado.",
            "agent_id": agent_id,
        }

    # ── 2. Evaluación de riesgo con LangGraph ────────────────────────────
    try:
        evaluacion = await evaluar_solicitud_prestamo(
            agent_id=agent_id,
            monto=monto,
            score=historial["score"],
            deuda_actual=historial["deuda_actual"],
        )
    except Exception as exc:
        logger.exception("Error en evaluación de riesgo para %s", agent_id)
        return {
            "error": True,
            "mensaje": f"Error durante la evaluación de riesgo: {exc}",
            "agent_id": agent_id,
        }

    if not evaluacion["aprobado"]:
        return {
            "estado": "rechazado",
            "agent_id": agent_id,
            "monto": monto,
            "motivo": evaluacion["motivo"],
            "score": evaluacion["score_utilizado"],
        }

    # ── 3. Transferencia on-chain ────────────────────────────────────────
    try:
        tx_result = await ejecutar_transferencia_prestamo(
            destinatario=agent_id,
            monto_usdc=monto,
        )
    except BlockchainError as exc:
        logger.error("Blockchain error para %s: %s", agent_id, exc)
        return {
            "estado": "error_blockchain",
            "agent_id": agent_id,
            "monto": monto,
            "mensaje": str(exc),
            "aprobado_internamente": True,
            "nota": "El préstamo fue aprobado pero la transacción en blockchain falló.",
        }
    except Exception as exc:
        logger.exception("Error inesperado en blockchain para %s", agent_id)
        return {
            "estado": "error_blockchain",
            "agent_id": agent_id,
            "monto": monto,
            "mensaje": f"Error inesperado en la transferencia: {exc}",
            "aprobado_internamente": True,
        }

    # ── 4. Registrar en DB ───────────────────────────────────────────────
    try:
        await registrar_prestamo(
            agent_id=agent_id,
            monto=monto,
            tx_hash=tx_result["tx_hash"],
            estado="aprobado",
        )
    except Exception as exc:
        logger.warning(
            "Préstamo transferido (TX %s) pero falló el registro en DB: %s",
            tx_result["tx_hash"],
            exc,
        )

    return {
        "estado": "aprobado",
        "agent_id": agent_id,
        "monto": monto,
        "tx_hash": tx_result["tx_hash"],
        "block_number": tx_result["block_number"],
        "red": "Base (L2)",
        "moneda": "USDC",
        "motivo": evaluacion["motivo"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.resource("bank://tasas_interes")
async def tasas_interes() -> dict[str, Any]:
    """Tasas de interés vigentes del banco RSoft.

    Devuelve las tasas actuales para distintos tipos de préstamo,
    incluyendo moneda (USDC), red (Base) y fecha de última actualización.
    """
    try:
        return await obtener_tasas_interes()
    except Exception as exc:
        logger.exception("Error al obtener tasas de interés")
        return {
            "error": True,
            "mensaje": f"No se pudieron obtener las tasas de interés: {exc}",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Launch the MCP server with the configured transport."""
    transport = settings.mcp_transport.lower()

    if transport == "sse":
        mcp.run(transport="sse", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
