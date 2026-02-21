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
    get_creditworthiness as _get_creditworthiness,
    get_interest_rates as _get_interest_rates,
    request_loan as _request_loan,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

# ── MCP Server instance ─────────────────────────────────────────────────────

_settings = get_settings()

mcp = FastMCP(
    "RSoft_Agentic_Bank",
    instructions=(
        "RSoft Latam intelligent banking server. "
        "Allows querying agent creditworthiness, requesting loans "
        "evaluated by AI and executed on the Base network (L2), "
        "and consulting current interest rates."
    ),
    host=_settings.mcp_host,
    port=_settings.mcp_port,
    stateless_http=True,
    streamable_http_path="/",
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS (free via MCP)
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def get_creditworthiness(agent_id: str) -> dict[str, Any]:
    """Query the creditworthiness and credit history of an agent.

    Use this tool when you need to:
    - Verify whether an agent has a good credit history.
    - Obtain the current credit score of an agent.
    - Check the outstanding debt of an agent before approving an operation.
    - Assess the risk of an agent prior to a loan request.

    Args:
        agent_id: Unique identifier of the agent in the banking system.
                  Example: "agent_0x1a2b3c".

    Returns:
        Dictionary with: agent_id, score (0-850), history (list of records),
        current_debt (float in USDC) and status ("active" | "delinquent" | "unregistered").
    """
    try:
        return await _get_creditworthiness(agent_id)
    except Exception:
        logger.exception("Error fetching creditworthiness for %s", agent_id)
        return {
            "error": True,
            "message": "Could not fetch the agent's creditworthiness.",
            "agent_id": agent_id,
        }


@mcp.tool()
async def request_loan(amount: float, agent_id: str) -> dict[str, Any]:
    """Request a loan that is evaluated by AI and, if approved, executes a
    USDC transfer on the Base network (L2).

    Use this tool when:
    - An agent needs USDC financing.
    - The full flow is required: risk evaluation → approval →
      on-chain transfer.
    - The agent has already been verified with `get_creditworthiness` and wants to proceed.

    Args:
        amount: Requested loan amount in USDC. Must be > 0.
                Example: 5000.00
        agent_id: Unique identifier of the requesting agent.
                  Example: "agent_0x1a2b3c".

    Returns:
        Dictionary with the request result:
        - If approved: includes tx_hash, block_number, amount, status "approved".
        - If rejected: includes rejection reason and status "rejected".
        - If error: includes error detail.
    """
    if amount <= 0:
        return {
            "error": True,
            "message": "Amount must be greater than 0.",
            "agent_id": agent_id,
        }

    try:
        return await _request_loan(agent_id=agent_id, amount=amount)
    except Exception:
        logger.exception("Error requesting loan for %s", agent_id)
        return {
            "error": True,
            "message": "Could not process the loan request.",
            "agent_id": agent_id,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES (free via MCP)
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.resource("bank://interest_rates")
async def interest_rates() -> dict[str, Any]:
    """Current interest rates for RSoft bank.

    Returns the current rates for different loan types,
    including currency (USDC), network (Base) and last update date.
    """
    try:
        return await _get_interest_rates()
    except Exception:
        logger.exception("Error fetching interest rates")
        return {
            "error": True,
            "message": "Could not fetch interest rates.",
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

    # Mount MCP app at /mcp (internal path is "/" via streamable_http_path)
    mcp_app = mcp.streamable_http_app()
    app.mount("/mcp", mcp_app)

    # Fix: Mangum/Lambda strips trailing slashes, causing a 307 redirect loop
    # on app.mount("/mcp"). This middleware adds the slash back before routing.
    @app.middleware("http")
    async def fix_mcp_trailing_slash(request, call_next):
        if request.url.path == "/mcp":
            request.scope["path"] = "/mcp/"
        return await call_next(request)

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
                "GET /paid/interest-rates": RouteConfig(
                    accepts=[
                        PaymentOption(
                            scheme="exact",
                            pay_to=_settings.bank_wallet_address,
                            price="$0.001",
                            network=network,
                        ),
                    ],
                    mime_type="application/json",
                    description="Current interest rates for RSoft bank",
                ),
                "POST /paid/loans": RouteConfig(
                    accepts=[
                        PaymentOption(
                            scheme="exact",
                            pay_to=_settings.bank_wallet_address,
                            price="$0.01",
                            network=network,
                        ),
                    ],
                    mime_type="application/json",
                    description="Request a USDC loan via RSoft Agentic Bank",
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
