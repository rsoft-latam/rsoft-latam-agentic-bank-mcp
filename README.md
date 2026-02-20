# rsoft-latam-agentic-bank-mcp

MCP Server proxy for **RSoft Agentic Bank** — exposes banking tools to LLM agents (Moltbook) via the Model Context Protocol, delegating all logic to the RSoft Agentic Bank backend.

## Architecture

```
Agentes Moltbook  →  MCP Server (this project)  →  Backend rsoft-agentic-bank
                     thin proxy / adapter             (LangGraph, Supabase, Base Network)
```

This server does **not** connect directly to Supabase, blockchain, or AI services. It acts as an MCP-compliant layer that forwards requests to the real backend via HTTP.

## Stack

- **FastMCP** — MCP server framework (STDIO, Streamable HTTP)
- **httpx** — Async HTTP client to communicate with the backend
- **Mangum** — ASGI adapter for AWS Lambda

## Quick start

```bash
# 1. Clone & install
git clone <repo-url> && cd rsoft-latam-agentic-bank-mcp
cp .env.example .env   # set BACKEND_URL
pip install -r requirements.txt

# 2. Run (STDIO — local/testing)
python -m app.main

# 3. Run (Streamable HTTP — server mode)
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python -m app.main
```

## Deploy on AWS Lambda

The server includes a Mangum handler ready for Lambda + API Gateway.

```
API Gateway  →  Lambda  →  Mangum  →  FastMCP (streamable-http)  →  Backend
```

**Lambda configuration:**

| Setting | Value |
|---|---|
| Runtime | Python 3.11+ |
| Handler | `app.main.lambda_handler` |
| Timeout | 120s (recommended) |

**Environment variables in Lambda:**

```
BACKEND_URL=https://your-backend.example.com/api/v1
```

**Steps:**

1. Package the project with dependencies into a `.zip` or container image
2. Create the Lambda function with handler `app.main.lambda_handler`
3. Set `BACKEND_URL` in the Lambda environment variables
4. Create an API Gateway (HTTP API) and route all traffic to the Lambda
5. The MCP endpoint will be available at your API Gateway URL

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `BACKEND_URL` | RSoft Agentic Bank backend base URL | `http://localhost:8080/api/v1` |
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_HOST` | Host to bind (HTTP mode) | `0.0.0.0` |
| `MCP_PORT` | Port to bind (HTTP mode) | `8000` |

## Transports

| Transport | Use case | How to run |
|---|---|---|
| `stdio` | Local development / testing | `python -m app.main` |
| `streamable-http` | HTTP server (direct or container) | `MCP_TRANSPORT=streamable-http python -m app.main` |
| Lambda | AWS Lambda + API Gateway | Handler: `app.main.lambda_handler` |

## MCP Tools

| Tool | Description |
|---|---|
| `get_creditworthiness(agent_id)` | Credit history & score for an agent |
| `request_loan(amount, agent_id)` | Full loan flow: risk eval, approval, on-chain transfer |

## MCP Resources

| URI | Description |
|---|---|
| `bank://interest_rates` | Current interest rates |

## Backend endpoints used

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/agents/{agent_id}/creditworthiness` | Fetch agent credit history |
| `POST` | `/loans` | Request a loan (`{agent_id, amount}`) |
| `GET` | `/interest-rates` | Fetch current interest rates |

## Project structure

```
app/
├── main.py             # MCP server (tools, resources, Lambda handler, entrypoint)
├── config.py           # Settings from .env / AWS env vars
└── backend_client.py   # httpx client to the real backend
```

## Docker Build

```bash
docker buildx create --name lambda-builder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -t rsoft-agentic-bank-mcp . --load
```

## Deploy to ECR

```bash
./deploy.sh
```
