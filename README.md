# rsoft-latam-agentic-bank-mcp

MCP Server for **RSoft Agentic Bank** — exposes banking tools to LLM agents via the Model Context Protocol.

## Stack

- **FastMCP** — MCP server framework (STDIO + SSE transports)
- **Supabase** — Credit history & loan records
- **LangGraph** — Loan risk-evaluation workflow
- **Web3.py** — USDC transfers on Base Network (L2)

## Quick start

```bash
# 1. Clone & install
git clone <repo-url> && cd rsoft-latam-agentic-bank-mcp
cp .env.example .env   # fill in your keys
pip install -e .

# 2. Run (STDIO — local/testing)
rsoft-bank-mcp

# 3. Run (SSE — production / AWS Lambda)
MCP_TRANSPORT=sse MCP_PORT=8000 rsoft-bank-mcp
```

## MCP Tools

| Tool | Description |
|---|---|
| `consultar_solvencia(agent_id)` | Credit history & score from Supabase |
| `solicitar_prestamo(monto, agent_id)` | Full loan flow: risk eval → blockchain transfer → DB record |

## MCP Resources

| URI | Description |
|---|---|
| `bank://tasas_interes` | Current interest rates |

## Project structure

```
src/rsoft_agentic_bank/
├── server.py              # MCP server (tools, resources, transport)
├── config.py              # Pydantic settings from .env
└── backend/
    ├── supabase_client.py # Supabase queries
    ├── langgraph_flow.py  # Loan risk evaluation graph
    └── blockchain.py      # Base Network USDC transfers
```
