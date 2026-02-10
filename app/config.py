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

# ── App Settings ────────────────────────────────────

APP_ENV = ENV
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


# ── Settings object ─────────────────────────────────

class _Settings:
    __slots__ = (
        "backend_url", "mcp_transport", "mcp_host", "mcp_port",
        "app_env", "log_level",
    )

    def __init__(self) -> None:
        self.backend_url = BACKEND_URL
        self.mcp_transport = MCP_TRANSPORT
        self.mcp_host = MCP_HOST
        self.mcp_port = MCP_PORT
        self.app_env = APP_ENV
        self.log_level = LOG_LEVEL


_settings = _Settings()


def get_settings() -> _Settings:
    return _settings
