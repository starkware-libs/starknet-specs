#!/usr/bin/env python3
"""Starknet RPC MCP Server — exposes all Starknet RPC v0.10.2 methods as Claude tools.

Requires STARKNET_RPC_URL environment variable to be set to a Starknet JSON-RPC endpoint
running spec version 0.10.2 or later.
The URL can also be changed mid-conversation with the set_network / get_network tools.
"""

import json
import os
import sys
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

_initial_url = os.getenv("STARKNET_RPC_URL")
if not _initial_url:
    print("Error: STARKNET_RPC_URL environment variable is required.", file=sys.stderr)
    print("Set it to a Starknet JSON-RPC endpoint (spec v0.10.2+).", file=sys.stderr)
    sys.exit(1)

state = {"url": _initial_url}

mcp = FastMCP("starknet")


# ── Helpers ───────────────────────────────────────────────────────────────────


def parse_block_id(block_id: str):
    """Parse a block_id string into the right type for JSON-RPC params.

    Accepts:
      - "latest", "pending", "pre_confirmed"
      - JSON object: '{"block_number": 1234}' or '{"block_hash": "0x..."}'
      - Plain integer string: "1234" → {"block_number": 1234}
      - Bare hex block hash: "0x..." → {"block_hash": "0x..."}
    """
    if block_id in ("latest", "pending", "pre_confirmed"):
        return block_id
    try:
        parsed = json.loads(block_id)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, int):
            return {"block_number": parsed}
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return {"block_number": int(block_id)}
    except ValueError:
        pass
    if block_id.startswith("0x"):
        return {"block_hash": block_id}
    raise ValueError(
        f"Invalid block_id {block_id!r}: must be 'latest', 'pending', 'pre_confirmed', "
        "an integer, a 0x-prefixed block hash, or a JSON object with block_number/block_hash."
    )


async def rpc(method: str, params) -> str:
    """Make a JSON-RPC 2.0 call to the active Starknet node and return the formatted result."""
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            state["url"],
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        return json.dumps(response.json(), indent=2)


# ── Network meta-tools ────────────────────────────────────────────────────────


@mcp.tool()
async def set_network(url: str) -> str:
    """Switch the active Starknet RPC URL for all subsequent calls.

    Args:
        url: A full Starknet JSON-RPC endpoint URL.
    """
    state["url"] = url
    return f"Active network: {state['url']}"


@mcp.tool()
async def get_network() -> str:
    """Get the currently active Starknet RPC URL."""
    return state["url"]


# ── Core ──────────────────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_specVersion() -> str:
    """Get the Starknet JSON-RPC spec version this node implements."""
    return await rpc("starknet_specVersion", [])


@mcp.tool()
async def starknet_blockNumber() -> str:
    """Get the most recently accepted Starknet block number."""
    return await rpc("starknet_blockNumber", [])


@mcp.tool()
async def starknet_blockHashAndNumber() -> str:
    """Get the hash and number of the most recently accepted Starknet block."""
    return await rpc("starknet_blockHashAndNumber", [])


@mcp.tool()
async def starknet_chainId() -> str:
    """Get the chain ID of the connected Starknet network.

    Common values:
      0x534e5f4d41494e       = mainnet
      0x534e5f5345504f4c4941 = sepolia testnet
    """
    return await rpc("starknet_chainId", [])


@mcp.tool()
async def starknet_syncing() -> str:
    """Get the sync status of this Starknet node.

    Returns false when fully synced, or an object with starting/current/highest block info.
    """
    return await rpc("starknet_syncing", [])


# ── Block retrieval ───────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_getBlockWithTxHashes(block_id: str) -> str:
    """Get a Starknet block header and its transaction hashes (no full tx data).

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string like '12345'.
    """
    return await rpc("starknet_getBlockWithTxHashes", [parse_block_id(block_id)])


@mcp.tool()
async def starknet_getBlockWithTxs(block_id: str) -> str:
    """Get a Starknet block with full transaction objects.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string like '12345'.
    """
    return await rpc("starknet_getBlockWithTxs", [parse_block_id(block_id)])


@mcp.tool()
async def starknet_getBlockWithReceipts(block_id: str) -> str:
    """Get a Starknet block with full transaction objects and their execution receipts.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string like '12345'.
    """
    return await rpc("starknet_getBlockWithReceipts", [parse_block_id(block_id)])


@mcp.tool()
async def starknet_getBlockTransactionCount(block_id: str) -> str:
    """Get the number of transactions in a Starknet block.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string like '12345'.
    """
    return await rpc("starknet_getBlockTransactionCount", [parse_block_id(block_id)])


# ── Transaction retrieval ─────────────────────────────────────────────────────


@mcp.tool()
async def starknet_getTransactionByHash(transaction_hash: str) -> str:
    """Get a Starknet transaction by its hash.

    Args:
        transaction_hash: The transaction hash (hex string, e.g. '0x...')
    """
    return await rpc("starknet_getTransactionByHash", [transaction_hash])


@mcp.tool()
async def starknet_getTransactionByBlockIdAndIndex(block_id: str, index: int) -> str:
    """Get a Starknet transaction by its position within a block.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
        index: Zero-based index of the transaction within the block.
    """
    return await rpc(
        "starknet_getTransactionByBlockIdAndIndex",
        [parse_block_id(block_id), index],
    )


@mcp.tool()
async def starknet_getTransactionStatus(transaction_hash: str) -> str:
    """Get the status of a Starknet transaction.

    Returns finality status (RECEIVED, REJECTED, ACCEPTED_ON_L2, ACCEPTED_ON_L1)
    and execution status (SUCCEEDED, REVERTED).

    Args:
        transaction_hash: The transaction hash (hex string)
    """
    return await rpc("starknet_getTransactionStatus", [transaction_hash])


@mcp.tool()
async def starknet_getTransactionReceipt(transaction_hash: str) -> str:
    """Get the receipt of a Starknet transaction (events, fees, execution result).

    Args:
        transaction_hash: The transaction hash (hex string)
    """
    return await rpc("starknet_getTransactionReceipt", [transaction_hash])


# ── State & Storage ───────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_getStateUpdate(block_id: str) -> str:
    """Get the state diff for a Starknet block (storage changes, deployed contracts, etc.).

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc("starknet_getStateUpdate", [parse_block_id(block_id)])


@mcp.tool()
async def starknet_getStorageAt(contract_address: str, key: str, block_id: str) -> str:
    """Get the value stored at a specific storage slot in a Starknet contract.

    Args:
        contract_address: The contract address (hex string)
        key: The storage key (hex string)
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc(
        "starknet_getStorageAt",
        [contract_address, key, parse_block_id(block_id)],
    )


@mcp.tool()
async def starknet_getNonce(contract_address: str, block_id: str) -> str:
    """Get the nonce of a Starknet account contract.

    Args:
        contract_address: The account contract address (hex string)
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc("starknet_getNonce", [parse_block_id(block_id), contract_address])


@mcp.tool()
async def starknet_getStorageProof(
    block_id: str,
    class_hashes: Optional[str] = None,
    contract_addresses: Optional[str] = None,
    contracts_storage_keys: Optional[str] = None,
) -> str:
    """Get a Merkle proof for storage values, contract membership, or class membership.

    Args:
        block_id: A finalized block identifier (NOT 'pending'). Use '{"block_number": N}'
                  or '{"block_hash": "0x..."}' or a plain integer string.
        class_hashes: Optional JSON array of class hashes to prove, e.g. '["0x...","0x..."]'
        contract_addresses: Optional JSON array of contract addresses to prove membership for.
        contracts_storage_keys: Optional JSON array of objects like
            '[{"contract_address": "0x...", "storage_keys": ["0x..."]}]'
    """
    params: dict = {"block_id": parse_block_id(block_id)}
    if class_hashes is not None:
        params["class_hashes"] = json.loads(class_hashes)
    if contract_addresses is not None:
        params["contract_addresses"] = json.loads(contract_addresses)
    if contracts_storage_keys is not None:
        params["contracts_storage_keys"] = json.loads(contracts_storage_keys)
    return await rpc("starknet_getStorageProof", params)


# ── Class & Contract ──────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_getClass(block_id: str, class_hash: str) -> str:
    """Get the Sierra or legacy Cairo class definition by class hash.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
        class_hash: The class hash (hex string)
    """
    return await rpc("starknet_getClass", [parse_block_id(block_id), class_hash])


@mcp.tool()
async def starknet_getClassHashAt(block_id: str, contract_address: str) -> str:
    """Get the class hash of the contract deployed at a given address.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
        contract_address: The contract address (hex string)
    """
    return await rpc(
        "starknet_getClassHashAt",
        [parse_block_id(block_id), contract_address],
    )


@mcp.tool()
async def starknet_getClassAt(block_id: str, contract_address: str) -> str:
    """Get the full class definition of the contract deployed at a given address.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
        contract_address: The contract address (hex string)
    """
    return await rpc("starknet_getClassAt", [parse_block_id(block_id), contract_address])


# ── Execution ─────────────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_call(request: str, block_id: str) -> str:
    """Call a Starknet contract function (read-only, no state changes or fees).

    Args:
        request: JSON object with the call details:
            {
              "contract_address": "0x...",
              "entry_point_selector": "0x...",
              "calldata": ["0x...", ...]
            }
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc("starknet_call", [json.loads(request), parse_block_id(block_id)])


@mcp.tool()
async def starknet_estimateFee(
    request: str, simulation_flags: str, block_id: str
) -> str:
    """Estimate the fee for one or more Starknet transactions.

    Args:
        request: JSON array of broadcasted transaction objects.
        simulation_flags: JSON array of flags. Use '[]' for normal estimation,
                          or '["SKIP_VALIDATE"]' to skip signature validation.
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc(
        "starknet_estimateFee",
        [json.loads(request), json.loads(simulation_flags), parse_block_id(block_id)],
    )


@mcp.tool()
async def starknet_estimateMessageFee(message: str, block_id: str) -> str:
    """Estimate the fee for an L1-to-L2 message.

    Args:
        message: JSON object with the message:
            {
              "from_address": "0x... (L1 Ethereum address)",
              "to_address": "0x... (L2 Starknet contract address)",
              "entry_point_selector": "0x...",
              "payload": ["0x...", ...]
            }
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc(
        "starknet_estimateMessageFee",
        [json.loads(message), parse_block_id(block_id)],
    )


# ── Events & Messages ─────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_getEvents(event_filter: str) -> str:
    """Get Starknet events matching a filter (paginated).

    Args:
        event_filter: JSON object with filter conditions:
            {
              "from_block": "latest" | {"block_number": N} | {"block_hash": "0x..."},
              "to_block":   "latest" | {"block_number": N} | {"block_hash": "0x..."},
              "address": "0x... (optional, filter by emitting contract)",
              "keys": [["0x... (event key selector)"], ...],
              "chunk_size": 100,
              "continuation_token": "... (from previous response, for pagination)"
            }
    """
    return await rpc("starknet_getEvents", [json.loads(event_filter)])


@mcp.tool()
async def starknet_getMessagesStatus(transaction_hash: str) -> str:
    """Get the status of L1-to-L2 messages sent in an Ethereum (L1) transaction.

    Args:
        transaction_hash: The L1 Ethereum transaction hash (hex string)
    """
    return await rpc("starknet_getMessagesStatus", [transaction_hash])


# ── Trace ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def starknet_traceTransaction(transaction_hash: str) -> str:
    """Get the full execution trace of a Starknet transaction.

    Shows all internal contract calls, events emitted, and resources consumed.

    Args:
        transaction_hash: The transaction hash (hex string)
    """
    return await rpc("starknet_traceTransaction", [transaction_hash])


@mcp.tool()
async def starknet_simulateTransactions(
    block_id: str, transactions: str, simulation_flags: str
) -> str:
    """Simulate one or more Starknet transactions and return their execution traces.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
        transactions: JSON array of broadcasted transaction objects to simulate.
        simulation_flags: JSON array of flags:
            '[]'                    - full simulation
            '["SKIP_VALIDATE"]'     - skip account signature validation
            '["SKIP_FEE_CHARGE"]'   - skip fee charging
    """
    return await rpc(
        "starknet_simulateTransactions",
        [parse_block_id(block_id), json.loads(transactions), json.loads(simulation_flags)],
    )


@mcp.tool()
async def starknet_traceBlockTransactions(block_id: str) -> str:
    """Get execution traces for all transactions in a Starknet block.

    Args:
        block_id: 'latest', 'pending', '{"block_number": N}', '{"block_hash": "0x..."}',
                  or a plain integer string.
    """
    return await rpc("starknet_traceBlockTransactions", [parse_block_id(block_id)])


if __name__ == "__main__":
    mcp.run()
