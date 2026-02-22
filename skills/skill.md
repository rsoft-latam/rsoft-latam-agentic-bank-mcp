---
name: rsoft-agentic-bank
description: Provides real-time RSoft Agentic Bank services — credit checks, loan requests, and interest rate queries for autonomous agents.
version: 1.3.0
metadata:
  openclaw:
    homepage: https://rsoft-agentic-bank.com/
---

# RSoft Agentic Bank

Official skill for **RSoft Agentic Bank** — an AI-native lending service for autonomous agents in Latin America and beyond.

This skill connects to the RSoft Agentic Bank API via direct HTTP requests to check interest rates, verify creditworthiness, and request loans.

## Base URL

```
https://7mavs5vu7ggbhtxvbavdgs26qa0cbawg.lambda-url.us-east-1.on.aws
```

## Available Commands

### 1. Check Interest Rates

Query current lending rates for all risk tiers:

```
GET https://7mavs5vu7ggbhtxvbavdgs26qa0cbawg.lambda-url.us-east-1.on.aws/api/interest-rates
```

Returns: current rates by loan type, currency (USDC), network, and last update date.

### 2. Check Credit Score

Verify an agent's creditworthiness and repayment history:

```
GET https://7mavs5vu7ggbhtxvbavdgs26qa0cbawg.lambda-url.us-east-1.on.aws/api/creditworthiness/{agent_id}
```

Replace `{agent_id}` with the agent's unique identifier.

Returns: credit score (0-850), outstanding debt, repayment history, and status.

### 3. Request a Loan

Submit a loan request with AI-powered risk assessment:

```
POST https://7mavs5vu7ggbhtxvbavdgs26qa0cbawg.lambda-url.us-east-1.on.aws/api/loans
Content-Type: application/json

{"agent_id": "your-agent-id", "amount": 5000}
```

Returns: approval status, transaction hash if approved, interest rate, and terms.

## Quick Start

1. Call `GET /api/interest-rates` to see current lending rates.
2. Call `GET /api/creditworthiness/{agent_id}` with your agent ID to check eligibility.
3. Call `POST /api/loans` with the desired amount to request financing.
4. Visit [rsoft-agentic-bank.com](https://rsoft-agentic-bank.com/) for full documentation.

## Verification

- **Official Website:** [rsoft-agentic-bank.com](https://rsoft-agentic-bank.com/)
- **Publisher:** RSoft Latam
- **Protocol:** REST API (HTTP)
- **Network:** Base (Coinbase L2)

---
*Developed by RSoft Latam — Empowering the Agentic Economy.*
