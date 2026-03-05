import os
from pathlib import Path
from dotenv import load_dotenv

# ── Environment detection ────────────────────────────

ENV = os.getenv("ENV", "local")

if ENV != "prod":
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
    print("Variables loaded from .env file")
else:
    print("Variables loaded from AWS")

# ── RSoft Agentic Bank Backend ───────────────────────

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080/api/v1")

# ── MCP Transport ───────────────────────────────────

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

# ── x402 Payments ──────────────────────────────────

BANK_WALLET_ADDRESS = os.environ.get("BANK_WALLET_ADDRESS", "")
X402_NETWORK_ID = os.environ.get("X402_NETWORK_ID", "base-sepolia")

# ── App Settings ────────────────────────────────────

APP_ENV = ENV
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


# ── Settings object ─────────────────────────────────

class _Settings:
    __slots__ = (
        "backend_url", "mcp_transport", "mcp_host", "mcp_port",
        "app_env", "log_level", "bank_wallet_address", "x402_network_id",
    )

    def __init__(self) -> None:
        self.backend_url = BACKEND_URL
        self.mcp_transport = MCP_TRANSPORT
        self.mcp_host = MCP_HOST
        self.mcp_port = MCP_PORT
        self.app_env = APP_ENV
        self.log_level = LOG_LEVEL
        self.bank_wallet_address = BANK_WALLET_ADDRESS
        self.x402_network_id = X402_NETWORK_ID


_settings = _Settings()


def get_settings() -> _Settings:
    return _settings
