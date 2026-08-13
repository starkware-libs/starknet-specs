# Starknet Specifications

This repository publishes different technical specifications pertaining to the implementation and interaction with Starknet.

## Specifications

| Spec                                       | Folder         | Version advertised by        |
| ------------------------------------------ | -------------- | ---------------------------- |
| [Full node JSON-RPC](./api/)               | `api/`         | `starknet_specVersion`       |
| [Wallet API](./wallet-api/wallet_rpc.json) | `wallet-api/`  | `wallet_supportedWalletApi`  |
| [Proving API](./proving-api/)              | `proving-api/` | the proving API version call |
| [P2P](./p2p/README.md)                     | `p2p/`         | –                            |

The full node JSON-RPC API can be viewed in the OpenRPC playground [here](https://playground.open-rpc.org/?uiSchema%5BappBar%5D%5Bui:splitView%5D=false&schemaUrl=https://raw.githubusercontent.com/starkware-libs/starknet-specs/master/api/starknet_api_openrpc.json&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:darkMode%5D=true&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false), and a guide to it is [here](./starknet_vs_ethereum_node_apis.md).

## Versioning and Releases

All files share one version number, but each release changes only one of the specs above. An implementation advertises the version of the latest release that changed its spec, so implementations may correctly report different versions.

This applies from `v0.10.4` onward. Earlier releases predate it and may have changed more than one spec.

The latest release that changed each spec:

| Spec               | Current version |
| ------------------ | --------------- |
| Full node JSON-RPC | `0.10.2`        |
| Wallet API         | `0.10.4-rc.0`   |
| Proving API        | `0.10.3`        |
| P2P                | `0.10.3`        |

## MCP Server (Claude Code)

An MCP server is available under `mcp/` that exposes all Starknet JSON-RPC methods as Claude Code tools. This lets Claude query blocks, transactions, state, and traces directly from a live Starknet node.

If you use Claude Code, run `/install-starknet-mcp <your-rpc-url>` from this repo to set it up. See [mcp/README.md](./mcp/README.md) for details.

# Tooling

When developing the schema, you can validate the OpenRPC schema file, by running the provided script.
Note this requires node.js installed.

The command:

```
./validate.js api/starknet_api_openrpc.json
```

will run a validation on the `api/starknet_api_openrpc.json` schema file.
If everything is ok, an appropriate message is displayed; otherwise errors are output to standard error.
