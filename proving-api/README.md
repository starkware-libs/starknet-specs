# Starknet proving API (`proving-api/`)

This directory defines the **Starknet transaction prover** JSON-RPC: how clients request proofs for transactions on top of a given block, separate from the public full-node read/write surface in `../api/`.

## Files

| File                                | Role                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| `starknet_proving_api_openrpc.json` | OpenRPC document for the proving API (e.g. `starknet_proveTransaction`, `starknet_specVersion`). |

External schema and error references use `./api/starknet_api_openrpc.json`, resolved from the **repository root** when running `validate.js` (same convention as `wallet-api/wallet_rpc.json`).

## Validation

From the repository root:

```bash
./validate.js proving-api/starknet_proving_api_openrpc.json
```

This file is included in `npm run validate_all`.

## Further reading

- [Node JSON-RPC](../api/README.md)
- [Repository overview](../README.md)
