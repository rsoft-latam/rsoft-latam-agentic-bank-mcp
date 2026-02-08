"""Centralised settings loaded from environment variables / .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # Base Network (blockchain)
    base_rpc_url: str = "https://mainnet.base.org"
    wallet_private_key: str = ""
    loan_contract_address: str = ""

    # LangGraph / OpenAI
    openai_api_key: str = ""

    # MCP Transport
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000


settings = Settings()  # type: ignore[call-arg]
