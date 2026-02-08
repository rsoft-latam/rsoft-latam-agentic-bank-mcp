"""Base Network (L2) blockchain interaction layer.

Handles USDC transfers for approved loans with comprehensive error handling
for failed transactions, gas estimation issues, and network problems.
"""

from __future__ import annotations

import logging
from typing import Any

from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound

from rsoft_agentic_bank.config import settings

logger = logging.getLogger(__name__)

# Minimal ERC-20 ABI (transfer + balanceOf)
ERC20_ABI: list[dict[str, Any]] = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]


class BlockchainError(Exception):
    """Raised when a blockchain operation fails."""


def _get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(settings.base_rpc_url))
    if not w3.is_connected():
        raise BlockchainError(
            f"No se pudo conectar al nodo RPC: {settings.base_rpc_url}"
        )
    return w3


async def ejecutar_transferencia_prestamo(
    destinatario: str,
    monto_usdc: float,
) -> dict[str, Any]:
    """Execute a USDC transfer on Base Network for an approved loan.

    Args:
        destinatario: The recipient wallet address (checksummed).
        monto_usdc: Amount in USDC (human-readable, e.g. 1000.50).

    Returns:
        Dict with tx_hash, status, block_number on success.

    Raises:
        BlockchainError: On any transaction or network failure.
    """
    try:
        w3 = _get_web3()
    except BlockchainError:
        raise
    except Exception as exc:
        raise BlockchainError(f"Error de conexión con la blockchain: {exc}") from exc

    try:
        contract_address = Web3.to_checksum_address(settings.loan_contract_address)
        to_address = Web3.to_checksum_address(destinatario)
    except Exception as exc:
        raise BlockchainError(f"Dirección inválida: {exc}") from exc

    contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)

    # USDC on Base uses 6 decimals
    amount_raw = int(monto_usdc * 10**6)

    account = w3.eth.account.from_key(settings.wallet_private_key)
    sender = account.address

    # ── Pre-flight checks ────────────────────────────────────────────────
    try:
        balance = contract.functions.balanceOf(sender).call()
        if balance < amount_raw:
            raise BlockchainError(
                f"Saldo insuficiente: {balance / 10**6:.2f} USDC disponible, "
                f"{monto_usdc:.2f} USDC requerido."
            )
    except BlockchainError:
        raise
    except Exception as exc:
        raise BlockchainError(f"Error al consultar balance: {exc}") from exc

    # ── Build, sign & send ───────────────────────────────────────────────
    try:
        nonce = w3.eth.get_transaction_count(sender)
        tx = contract.functions.transfer(to_address, amount_raw).build_transaction(
            {
                "from": sender,
                "nonce": nonce,
                "gas": 100_000,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
                "chainId": 8453,  # Base Mainnet
            }
        )
    except ContractLogicError as exc:
        raise BlockchainError(f"Lógica del contrato rechazó la TX: {exc}") from exc
    except Exception as exc:
        raise BlockchainError(f"Error al construir la transacción: {exc}") from exc

    try:
        signed = w3.eth.account.sign_transaction(tx, settings.wallet_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except Exception as exc:
        raise BlockchainError(f"Error al firmar/enviar la transacción: {exc}") from exc

    # ── Wait for receipt ─────────────────────────────────────────────────
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except TransactionNotFound:
        raise BlockchainError(
            f"Transacción {tx_hash.hex()} no encontrada después de 120 s."
        )
    except Exception as exc:
        raise BlockchainError(
            f"Error esperando confirmación de TX {tx_hash.hex()}: {exc}"
        ) from exc

    if receipt["status"] != 1:
        raise BlockchainError(
            f"Transacción revertida on-chain. TX hash: {tx_hash.hex()}"
        )

    logger.info("Préstamo transferido — TX %s confirmada en bloque %s", tx_hash.hex(), receipt["blockNumber"])

    return {
        "tx_hash": tx_hash.hex(),
        "status": "confirmada",
        "block_number": receipt["blockNumber"],
        "monto_usdc": monto_usdc,
        "destinatario": to_address,
    }
