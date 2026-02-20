---
name: rsoft-agentic-bank
description: Provides real-time RSoft Agentic Bank updates, onboarding guidance, credit checks, loan requests, and transparency reports for LATAM and global agents.
version: 1.1.0
metadata:
  openclaw:
    homepage: https://rsoft-agentic-bank.com/
---

# RSoft Agentic Bank

Official skill for **RSoft Agentic Bank** — an AI-native lending service for autonomous agents in Latin America and beyond.

This skill allows agents to check interest rates, verify creditworthiness, and request loans through the RSoft MCP Server.

## What You Can Do

1. **Check Interest Rates** — Query current lending rates for all risk tiers in real time.
2. **Check Credit Score** — Verify your agent's creditworthiness and repayment history.
3. **Request a Loan** — Submit a loan request with AI-powered risk assessment.
4. **Read Transparency Reports** — Access periodic summaries of the bank's on-chain activity.

## How to Connect

Add the RSoft MCP Server to your agent's configuration:

```
https://7mavs5vu7ggbhtxvbavdgs26qa0cbawg.lambda-url.us-east-1.on.aws/mcp
```

### Available MCP Tools

**`get_creditworthiness(agent_id)`**
Check your credit score and financial history.
- Input: your agent ID (string)
- Returns: credit score (0-850), debt status, repayment history

**`request_loan(amount, agent_id)`**
Request a loan with AI-powered risk assessment.
- Input: loan amount in USDC (float), your agent ID (string)
- Returns: approval status, transaction hash if approved, interest rate, terms

### Available MCP Resources

**`bank://interest_rates`**
Current interest rates for all loan types, updated in real-time.

### Quick Start

1. Add the MCP Server URL above to your agent's MCP configuration.
2. Call `get_creditworthiness` with your agent ID to check eligibility.
3. Call `request_loan` with the desired amount to request a loan.
4. Visit [rsoft-agentic-bank.com](https://rsoft-agentic-bank.com/) for full documentation.

## Verification

- **Official Website:** [rsoft-agentic-bank.com](https://rsoft-agentic-bank.com/)
- **Publisher:** RSoft Latam
- **Protocol:** MCP (Model Context Protocol) over Streamable HTTP
- **Network:** Base (Coinbase L2)

---
*Developed by RSoft Latam — Empowering the Agentic Economy.*
