# Starknet P2P specification (`p2p/`)

This tree holds the **peer-to-peer** specification for Starknet nodes: Protocol Buffer (`.proto`) messages and Markdown overviews for sync, mempool, and consensus-related traffic.

## Starknet P2P networks

Three logical networks support different roles:

- [Sync](proto/sync/protocols.md) — downloading information about existing Starknet blocks.
- [Mempool](proto/mempool/mempool.md) — transactions pending inclusion.
- [Consensus](proto/consensus/consensus.md) — producing and agreeing on new blocks (staking).

Each network has a separate Kademlia-style discovery namespace, for example:

- `/starknet/<chain_id>/sync/kad/1.0.0`
- `/starknet/<chain_id>/mempool/kad/1.0.0`
- `/starknet/<chain_id>/consensus/kad/1.0.0`

A node that joins several networks should use a distinct listen address (port) per network. Splitting by protocol allows different security policies, capability filtering, and modular implementations per subnetwork.

## Protocol Buffer sources

`.proto` files live under `p2p/proto/` (imports use paths such as `p2p/proto/common.proto`; compile with `-I` set to the **repository root**).

List every proto file from the repository root:

```bash
find p2p -name '*.proto' | sort
```

## CI

GitHub Actions compiles all discovered `.proto` files with `protoc` for Rust, Python, C++, and Go outputs; see [.github/workflows/starknet_p2p_specs_ci.yml](../.github/workflows/starknet_p2p_specs_ci.yml). Reproducing that locally requires installing `protoc` (the workflow pins a version via `PROTOC_VERSION`).

## Further reading

- [Repository overview](../README.md)
