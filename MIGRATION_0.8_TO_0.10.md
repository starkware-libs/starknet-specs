# Starknet RPC Migration Guide: v0.8 → v0.10 (latest)

This guide is for apps that already work against RPC v0.8 and need to keep the same functionality under v0.10.2 (the latest stable release). It is cumulative — it covers all breaking changes from both v0.9 and v0.10.

---

## 1. Rename every `"pending"` block tag to `"pre_confirmed"`

The `"pending"` block tag is gone. Replace it everywhere you pass a `BLOCK_ID` or `BLOCK_TAG`.

```diff
- { "block_tag": "pending" }
+ { "block_tag": "pre_confirmed" }
```

This affects every method that accepts a `block_id` parameter:
`starknet_getBlockWithTxHashes`, `starknet_getBlockWithTxs`, `starknet_getBlockWithReceipts`, `starknet_getStateUpdate`, `starknet_getStorageAt`, `starknet_getClassAt`, `starknet_getNonce`, etc.

---

## 2. Update transaction status handling (`starknet_getTransactionStatus`)

### What changed

In v0.8 there was a single `finality_status` field that covered both finality and execution outcomes, and `"REJECTED"` was a valid value.

The response is now split into two **required** fields:

| Field | Type | Values |
|---|---|---|
| `finality_status` | `TXN_FINALITY_STATUS` | `PRE_CONFIRMED`, `ACCEPTED_ON_L2`, `ACCEPTED_ON_L1` |
| `execution_status` | `TXN_EXECUTION_STATUS` | `SUCCEEDED`, `REVERTED` |

### Migration

**Check for rejection:** `"REJECTED"` no longer exists. A failed transaction now shows `execution_status = "REVERTED"` with a `failure_reason` string.

```diff
- if (status.finality_status === "REJECTED") { handleRejected(status.failure_reason); }
+ if (status.execution_status === "REVERTED") { handleReverted(status.failure_reason); }
```

**Check for success:** Guard on both fields:

```diff
- if (status.finality_status === "ACCEPTED_ON_L2") { handleSuccess(); }
+ if (status.finality_status === "ACCEPTED_ON_L2" && status.execution_status === "SUCCEEDED") { handleSuccess(); }
```

**Note on `CANDIDATE` status:** The spec introduces `CANDIDATE` as a transaction status (a tx in the block-builder mempool). The feeder gateway does not return `CANDIDATE` transactions regardless of RPC version — do not rely on receiving it via the feeder gateway.

---

## 3. Update transaction receipt handling

### `block_number` is now always present

`TXN_RECEIPT_WITH_BLOCK_INFO` now includes a required `block_number` in all receipts. Any null-guards on `block_number` can be removed, but they will not break if kept.

### `failure_reason` scope narrowed

`failure_reason` now only appears when `execution_status === "REVERTED"`. If you previously checked it on `REJECTED` transactions, update that logic.

---

## 4. Update `starknet_estimateMessageFee` response parsing

The return type changed from `FEE_ESTIMATE` to `MESSAGE_FEE_ESTIMATE`. The fee unit for message fee estimates is always `WEI`. Update any code that asserts the unit is `FRI` for this method.

---

## 5. Update `starknet_getEvents` response parsing — `transaction_index` and `event_index` now required

The `EMITTED_EVENT` schema now has two additional **required** fields:

| Field | Description |
|---|---|
| `transaction_index` | Index of the transaction in the block that emitted this event |
| `event_index` | Index of the event within that transaction |

If you deserialize `starknet_getEvents` results into a strict struct, add these two fields.

---

## 6. WebSocket: replace `subscribePendingTransactions`

`starknet_subscribePendingTransactions` and its notification `starknet_subscriptionPendingTransactions` are **removed**. Two new subscriptions replace them:

### `starknet_subscribeNewTransactionReceipts`

Fires a full `TXN_RECEIPT_WITH_BLOCK_INFO` for each finality status update.

```json
{
  "method": "starknet_subscribeNewTransactionReceipts",
  "params": {
    "finality_status": ["ACCEPTED_ON_L2"],
    "sender_address": ["0x..."]
  }
}
```

- `finality_status` defaults to `["ACCEPTED_ON_L2"]` — direct replacement for the old subscription if you were watching confirmed transactions.
- Notification method: `starknet_subscriptionNewTransactionReceipts`

### `starknet_subscribeNewTransactions`

Fires a transaction with its current finality status.

```json
{
  "method": "starknet_subscribeNewTransactions",
  "params": {
    "finality_status": ["ACCEPTED_ON_L2"],
    "sender_address": ["0x..."]
  }
}
```

- Notification method: `starknet_subscriptionNewTransaction`
- Payload is `TXN_WITH_HASH` plus a `finality_status` field.

---

## 7. WebSocket: `starknet_subscriptionEvents` notification now includes `finality_status`

The notification payload now has a required `finality_status` field. If you deserialize this into a strict struct, add the field.

---

## 8. WebSocket: `starknet_unsubscribe` parameter type

The `subscription_id` parameter changed from a plain `integer` to a `SUBSCRIPTION_ID` type. In practice the value is still an integer; no change needed unless you type-check the schema directly.

---

## 9. Block header — new required commitment fields

`BLOCK_HEADER` now includes four additional **required** fields. If you deserialize block headers into a strict struct, add them:

| Field | Description |
|---|---|
| `event_commitment` | Merkle root for events in the block |
| `transaction_commitment` | Merkle root for transactions |
| `receipt_commitment` | Merkle root for receipts |
| `state_diff_commitment` | Merkle root for the state diff |

For old blocks where the data is unavailable, the value is `0x0`.

---

## 10. `PRE_CONFIRMED_BLOCK_HEADER` structure change

The pre-confirmed block header replaced `parent_hash` with `block_number`. If you parse pre-confirmed block headers directly:

```diff
- header.parent_hash
+ header.block_number   // local node's view of the height being built
```

---

## Schemas renamed (update any hardcoded `$ref` strings)

| v0.8 name | v0.10 name |
|---|---|
| `PENDING_BLOCK_HEADER` | `PRE_CONFIRMED_BLOCK_HEADER` |
| `PENDING_BLOCK_WITH_TX_HASHES` | `PRE_CONFIRMED_BLOCK_WITH_TX_HASHES` |
| `PENDING_BLOCK_WITH_TXS` | `PRE_CONFIRMED_BLOCK_WITH_TXS` |
| `PENDING_BLOCK_WITH_RECEIPTS` | `PRE_CONFIRMED_BLOCK_WITH_RECEIPTS` |
| `PENDING_STATE_UPDATE` | `PRE_CONFIRMED_STATE_UPDATE` |

---

## New features (optional — only relevant if you want them)

### `l1_accepted` block tag

A third block tag `"l1_accepted"` refers to the latest Starknet block that was both included in an L1 state update **and** finalized by L1 consensus. Useful when you need stronger finality than `"latest"`.

### Pre-confirmed block access

Query the block currently being built by the sequencer using `"pre_confirmed"` as a block tag.

### Subscribe to pre-confirmed events

`starknet_subscribeEvents` accepts an optional `finality_status` parameter. Pass `"PRE_CONFIRMED"` to receive events before L2 finality. The same event may fire multiple times as its status progresses.

### Subscribe to pre-confirmed transactions / receipts

Pass `"PRE_CONFIRMED"` in the `finality_status` array of `starknet_subscribeNewTransactionReceipts` or `starknet_subscribeNewTransactions`.

### `response_flags` on block and transaction queries (v0.10)

Several read methods now accept an optional `response_flags` array. Currently the only flag is `"INCLUDE_PROOF_FACTS"`, which adds a `proof_facts` field to INVOKE v3 transaction responses. Omitting `response_flags` (or passing an empty array) gives you the same response as before.

Methods that accept `response_flags`:
- `starknet_getBlockWithTxHashes`
- `starknet_getBlockWithTxs`
- `starknet_getTransaction`
- `starknet_getTransactionByBlockIdAndIndex`

### `starknet_getStorageAt` with `INCLUDE_LAST_UPDATE_BLOCK` (v0.10)

Pass `response_flags: ["INCLUDE_LAST_UPDATE_BLOCK"]` to get back a `STORAGE_RESULT` object:

```json
{
  "value": "0x...",
  "last_update_block": 12345
}
```

Without the flag the response is the same plain `FELT` as before.

### `starknet_getStateUpdate` with contract address filter (v0.10)

Pass an optional `contract_addresses` array to receive only the state diff entries for those contracts.

### `starknet_getEvents` — filter by multiple addresses (v0.10)

The `address` field in the event filter now accepts either a single address or an array of addresses.

### `starknet_traceBlockTransactions` — `RETURN_INITIAL_READS` flag (v0.10)

Pass `trace_flags: ["RETURN_INITIAL_READS"]` to receive the full set of initial state reads alongside the traces. Useful for building execution witnesses.

### WebSocket `starknet_subscribeNewTransactions` — `INCLUDE_PROOF_FACTS` tag (v0.10)

Pass `tags: ["INCLUDE_PROOF_FACTS"]` on the subscription to include proof facts in the transaction notification payload (INVOKE v3 only).
