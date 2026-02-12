"""RSoft Agentic Bank — MCP Server + x402 Paid REST API.

Thin proxy layer that exposes banking tools and resources to LLM agents
via the Model Context Protocol, delegating all logic to the RSoft Agentic
Bank backend.

Additionally serves paid REST endpoints at /paid/* that require x402
USDC micropayments on Base (Coinbase L2).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from app.backend_client import (
    consultar_solvencia as _consultar_solvencia,
    obtener_tasas_interes as _obtener_tasas_interes,
    solicitar_prestamo as _solicitar_prestamo,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

# ── MCP Server instance ─────────────────────────────────────────────────────

_settings = get_settings()

mcp = FastMCP(
    "RSoft_Agentic_Bank",
    instructions=(
        "Servidor bancario inteligente de RSoft Latam. "
        "Permite consultar solvencia crediticia de agentes, solicitar préstamos "
        "que se evalúan con IA y se ejecutan en la red Base (L2), "
        "y consultar las tasas de interés vigentes."
    ),
    host=_settings.mcp_host,
    port=_settings.mcp_port,
    stateless_http=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS (free via MCP)
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
        return await _consultar_solvencia(agent_id)
    except Exception as exc:
        logger.exception("Error al consultar solvencia para %s", agent_id)
        return {
            "error": True,
            "mensaje": "No se pudo consultar la solvencia del agente.",
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
    if monto <= 0:
        return {
            "error": True,
            "mensaje": "El monto debe ser mayor a 0.",
            "agent_id": agent_id,
        }

    try:
        return await _solicitar_prestamo(agent_id=agent_id, monto=monto)
    except Exception as exc:
        logger.exception("Error al solicitar préstamo para %s", agent_id)
        return {
            "error": True,
            "mensaje": "No se pudo procesar la solicitud de préstamo.",
            "agent_id": agent_id,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES (free via MCP)
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.resource("bank://tasas_interes")
async def tasas_interes() -> dict[str, Any]:
    """Tasas de interés vigentes del banco RSoft.

    Devuelve las tasas actuales para distintos tipos de préstamo,
    incluyendo moneda (USDC), red (Base) y fecha de última actualización.
    """
    try:
        return await _obtener_tasas_interes()
    except Exception as exc:
        logger.exception("Error al obtener tasas de interés")
        return {
            "error": True,
            "mensaje": "No se pudieron obtener las tasas de interés.",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED FASTAPI APP (MCP + paid REST + x402 middleware)
# ═══════════════════════════════════════════════════════════════════════════════


def _build_combined_app() -> FastAPI:
    """Build a FastAPI app that serves both MCP and paid REST endpoints."""
    from app.paid_routes import paid_router

    app = FastAPI(
        title="RSoft Agentic Bank — MCP + Paid API",
        version="1.27.0",
    )

    # Mount paid REST routes
    app.include_router(paid_router)

    # Mount MCP app at /mcp
    mcp_app = mcp.streamable_http_app()
    app.mount("/mcp", mcp_app)

    # Add x402 payment middleware if wallet is configured
    if _settings.bank_wallet_address:
        try:
            from x402.http import (
                FacilitatorConfig,
                HTTPFacilitatorClient,
                PaymentOption,
            )
            from x402.http.middleware.fastapi import PaymentMiddlewareASGI
            from x402.http.types import RouteConfig
            from x402.mechanisms.evm.exact import ExactEvmServerScheme
            from x402.server import x402ResourceServer

            facilitator = HTTPFacilitatorClient(
                FacilitatorConfig(url="https://x402.org/facilitator")
            )

            server = x402ResourceServer(facilitator)
            # Base Sepolia = eip155:84532, Base Mainnet = eip155:8453
            network = (
                "eip155:84532"
                if "sepolia" in _settings.x402_network_id
                else "eip155:8453"
            )
            server.register(network, ExactEvmServerScheme())

            routes = {
                "GET /paid/tasas-interes": RouteConfig(
                    accepts=[
                        PaymentOption(
                            scheme="exact",
                            pay_to=_settings.bank_wallet_address,
                            price="$0.001",
                            network=network,
                        ),
                    ],
                    mime_type="application/json",
                    description="Tasas de interés vigentes del banco RSoft",
                ),
                "POST /paid/prestamo": RouteConfig(
                    accepts=[
                        PaymentOption(
                            scheme="exact",
                            pay_to=_settings.bank_wallet_address,
                            price="$0.01",
                            network=network,
                        ),
                    ],
                    mime_type="application/json",
                    description="Solicitar préstamo USDC via RSoft Agentic Bank",
                ),
            }

            app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)
            logger.info(
                "x402 middleware enabled: payTo=%s network=%s",
                _settings.bank_wallet_address,
                network,
            )

        except ImportError:
            logger.warning("x402 library not installed — paid endpoints unprotected")
        except Exception:
            logger.exception("Failed to initialize x402 middleware")
    else:
        logger.warning("BANK_WALLET_ADDRESS not set — paid endpoints unprotected")

    # Health endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "rsoft-agentic-bank-mcp",
            "x402_enabled": bool(_settings.bank_wallet_address),
            "pay_to": _settings.bank_wallet_address or None,
        }

    return app


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Launch the MCP server with the configured transport."""
    transport = _settings.mcp_transport.lower()

    if transport == "sse":
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


# ── AWS Lambda handler ───────────────────────────────────────────────────────

try:
    from mangum import Mangum

    # Build the combined app (MCP + paid routes + x402)
    _combined_app = _build_combined_app()

    def lambda_handler(event, context):
        # Reset MCP session manager per invocation
        mcp._session_manager = None

        handler = Mangum(_combined_app, lifespan="off")
        return handler(event, context)

except ImportError:
    lambda_handler = None


if __name__ == "__main__":
    main()
