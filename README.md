# Starknet specifications

This repository publishes technical specifications for Starknet: full-node JSON-RPC, wallet JSON-RPC, transaction proving JSON-RPC, and peer-to-peer protocols for node and sequencer stacks.

| Area                                      | Details                                 |
| ----------------------------------------- | --------------------------------------- |
| [Node JSON-RPC](api/README.md)            | `api/` — OpenRPC documents and releases |
| [Wallet JSON-RPC](wallet-api/README.md)   | `wallet-api/` — dapp ↔ wallet surface  |
| [Proving JSON-RPC](proving-api/README.md) | `proving-api/` — transaction prover API |
| [P2P protocols](p2p/README.md)            | `p2p/` — Protocol Buffers and docs      |

For a high-level comparison between Starknet’s node API and common Ethereum node APIs, see [starknet_vs_ethereum_node_apis.md](./starknet_vs_ethereum_node_apis.md).

The main read API is easy to browse in the [OpenRPC playground](https://playground.open-rpc.org/?uiSchema%5BappBar%5D%5Bui:splitView%5D=false&schemaUrl=https://raw.githubusercontent.com/starkware-libs/starknet-specs/master/api/starknet_api_openrpc.json&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:darkMode%5D=true&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false).

## Tooling (Node.js)

From the repository root, after installing dependencies:

```bash
npm ci
```

Validate every OpenRPC document under `api/` (except `starknet_metadata.json`), plus `wallet-api/wallet_rpc.json` and `proving-api/starknet_proving_api_openrpc.json`:

```bash
npm run validate_all
```

Additional checks used in CI:

```bash
npm run check_component_uniqueness
npm run format_check
```

Apply formatting with `npm run format` when you change Markdown or JSON that Prettier covers.

## Optional: MCP helper

An MCP server that exposes Starknet JSON-RPC as tools lives under `mcp/`; see [mcp/README.md](./mcp/README.md).
