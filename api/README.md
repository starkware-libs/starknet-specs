# Starknet node API (`api/`)

This directory holds the **Starknet full-node JSON-RPC** specifications and related JSON artifacts used by nodes, indexers, and SDKs.

## Files

| File                              | Role                                                                                                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `starknet_api_openrpc.json`       | Core read API (blocks, state, classes, events, proofs, etc.).                                                                  |
| `starknet_write_api.json`         | Write-side methods (merged or referenced with the main document in releases).                                                  |
| `starknet_trace_api_openrpc.json` | Trace and simulation methods.                                                                                                  |
| `starknet_ws_api.json`            | WebSocket subscription API.                                                                                                    |
| `starknet_executables.json`       | Executable / compiler artifact metadata used with the API.                                                                     |
| `starknet_metadata.json`          | Supplementary metadata (skipped by `validate_all`; not a standalone OpenRPC file in CI).                                       |
| `release.md`                      | **Release process**: draft → release candidate → recommendation, semver tagging, and synchronized versions across these files. |

## Releases and versioning

All specification JSON files here are versioned **together** as one logical node API release. When you bump the spec, update the `"version"` field in each affected document and align `package.json` as described in `release.md`.

## Validation

From the repository root, `npm run validate_all` validates every `api/*.json` OpenRPC file except `starknet_metadata.json`, and also validates `wallet-api/wallet_rpc.json` and `proving-api/starknet_proving_api_openrpc.json`.

To validate only the main read document:

```bash
./validate.js api/starknet_api_openrpc.json
```

## Further reading

- [starknet_vs_ethereum_node_apis.md](../starknet_vs_ethereum_node_apis.md)
- [Repository overview](../README.md)
