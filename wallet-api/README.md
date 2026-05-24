# Starknet wallet API (`wallet-api/`)

This directory defines the **Starknet wallet JSON-RPC** used between dapps and an injected wallet provider. It complements the full-node JSON-RPC in `../api/`: wallets handle consent, signing, and network selection and often proxy chain reads to an RPC endpoint.

## Files

| File              | Role                                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `wallet_rpc.json` | OpenRPC document for wallet methods (capabilities, accounts, chain switching, typed data signing, invoke/declare and related flows, etc.). |

Wallet methods use the `wallet_` prefix (for example `wallet_requestAccounts`, `wallet_addInvokeTransaction`). Shared types may reference schemas under `../api/`.

## Validation

From the repository root:

```bash
./validate.js wallet-api/wallet_rpc.json
```

This file is also included in `npm run validate_all` (see [../api/README.md](../api/README.md)).

## Further reading

- [Repository overview](../README.md)
