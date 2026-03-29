# Starknet MCP Server

An MCP (Model Context Protocol) server that exposes all Starknet JSON-RPC v0.10.2 methods as Claude Code tools. Lets Claude read blocks, transactions, state, traces, and more directly from a live Starknet node.

## Installation

### Prerequisites

- Python 3.10+
- A Starknet JSON-RPC endpoint URL (any node implementing spec v0.10.2+)

### Using Claude Code (recommended)

If you have Claude Code, run the slash command from this repo:

```
/install-starknet-mcp <your-rpc-url>
```

This installs dependencies and registers the server automatically.

### Manual Setup

1. Install the Python dependencies:

```bash
pip install -r mcp/requirements.txt
```

2. Register the MCP server with Claude Code. You can install it in two scopes:

**Project-only** (available only in this repo):

```bash
claude mcp add --env STARKNET_RPC_URL=<your-rpc-url> starknet -- python mcp/server.py
```

**Global** (available in all your projects — recommended if you work with Starknet across multiple repos):

```bash
claude mcp add --scope user --env STARKNET_RPC_URL=<your-rpc-url> starknet -- python /absolute/path/to/mcp/server.py
```

Replace `<your-rpc-url>` with your Starknet JSON-RPC endpoint (v0.10.2+).

3. Restart Claude Code for the server to take effect.

## Available Tools

Once installed, Claude has access to all Starknet JSON-RPC read and trace methods:

**Blocks**: `starknet_getBlockWithTxHashes`, `starknet_getBlockWithTxs`, `starknet_getBlockWithReceipts`, `starknet_getBlockTransactionCount`, `starknet_blockNumber`, `starknet_blockHashAndNumber`

**Transactions**: `starknet_getTransactionByHash`, `starknet_getTransactionByBlockIdAndIndex`, `starknet_getTransactionStatus`, `starknet_getTransactionReceipt`

**State**: `starknet_getStateUpdate`, `starknet_getStorageAt`, `starknet_getNonce`, `starknet_getStorageProof`

**Contracts**: `starknet_getClass`, `starknet_getClassHashAt`, `starknet_getClassAt`

**Execution**: `starknet_call`, `starknet_estimateFee`, `starknet_estimateMessageFee`

**Events**: `starknet_getEvents`, `starknet_getMessagesStatus`

**Traces**: `starknet_traceTransaction`, `starknet_simulateTransactions`, `starknet_traceBlockTransactions`

**Node info**: `starknet_specVersion`, `starknet_chainId`, `starknet_syncing`

**Network management**: `set_network` (switch RPC URL mid-conversation), `get_network` (show current URL)

## Switching Networks

To switch to a different endpoint mid-conversation, ask Claude to use the `set_network` tool with a new URL. To check the current endpoint, use `get_network`.

## Running Tests

```bash
cd mcp
pip install -r requirements-dev.txt

# Unit tests (no network calls)
STARKNET_RPC_URL=http://unused pytest tests/test_server.py -m "not integration" -v

# Integration tests (live RPC)
STARKNET_RPC_URL=<your-rpc-url> pytest tests/test_server.py -m integration -v
```
