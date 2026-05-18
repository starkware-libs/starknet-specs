# STRK20 Wallet API — Design Decisions

Working notes for a new wallet API covering the STRK20 privacy protocol. Captures decisions made during brainstorming; open questions are flagged at the end.

## Method naming

- Use the `wallet_strk20*` prefix (named after the STRK20 privacy protocol, not generic "private").
- `wallet_strk20InvokeTransaction` — submit actions (mirrors `wallet_addInvokeTransaction`).
- `wallet_strk20Balances` — query balances for a list of token addresses.
- `wallet_strk20Mode` — query whether the address returned by `wallet_requestAccounts` is real or a generated random one.

Rejected alternatives:

- A single `wallet_strk20` method with multi-purpose params. Reads and writes should be separate: different return types, different error semantics.
- Per-action methods (`wallet_strk20Deposit`, `wallet_strk20Withdraw`, ...). API bloat; 1–2 actions fit fine in an array.
- A client-side builder pattern. Adds complexity without benefit given small action counts.

## Action shape

Flat array of action objects, not grouped-by-token. Most calls have 1–2 actions, and a flat array matches the existing `wallet_addInvokeTransaction` pattern.

Example:

```json
[
  { "type": "withdraw", "token": "0x...", "amount": 10, "recipient": "0x..." },
  { "type": "transfer", "token": "0x...", "amount": 11, "recipient": "0x..." }
]
```

## Action types (v1 scope)

- **deposit** — `{ type, token, amount }`. Always to self (no `recipient` field; can be added later).
- **withdraw** — `{ type, token, amount, recipient }`. `recipient` always explicit (no default-to-self).
- **transfer** — `{ type, token, amount, recipient }`. Private transfer to another user.
- **invoke / swap** — **deferred** to a later version. Needs cross-referencing (placeholders for open note IDs, pool address) between actions, which adds significant complexity. Deposit + withdraw + transfer cover the core privacy use cases.

## Registration

Handled transparently by the wallet — no explicit `register` action. If the user isn't registered, the wallet returns a `NOT_REGISTERED` error telling them to register first and come back.

## Return type

`wallet_strk20InvokeTransaction` returns `{ transaction_hash }`, same as `wallet_addInvokeTransaction`.

The dapp must tolerate long-running calls — proof generation takes time. No special async mechanism is introduced; the RPC call just takes longer than a normal transaction submission.

## Privacy mode and address handling

- No explicit mode-setter method.
- When a dapp calls `wallet_requestAccounts`, the wallet asks the user whether to return the real address or a freshly generated one.
- `wallet_strk20Mode` is read-only — it lets the dapp know whether the current address is real or generated, so the UI can adapt (e.g. show a "private mode" indicator).
- If the real address was already shared and the dapp then calls `wallet_strk20InvokeTransaction`, the wallet warns the user but doesn't block — they may still want to use private transfers even with reduced privacy.

## Non-privacy-aware dapp flow

A key goal: existing dapps (e.g. a DEX) should work with privacy without knowing about STRK20 at all.

Flow:

1. The dapp calls `wallet_requestAccounts` as usual.
2. The wallet generates a fresh address and offers to fund it by withdrawing from the privacy pool.
3. The user interacts with the dapp normally — public transactions from the generated address via `wallet_addInvokeTransaction`.
4. When the session ends, the wallet offers to sweep leftover funds back into the privacy pool.

The dapp does nothing special. All the privacy mechanics live in the wallet UI.

## ERC20 handling

Tokens are referenced by address only (type `ADDRESS` / `FELT`). No need for the `ASSET` structure used by `wallet_watchAsset` — the privacy pool contract handles token interaction internally.

## Errors

Tentative set:

New:

- `NOT_REGISTERED` — user hasn't registered in the privacy pool.
- `INSUFFICIENT_PRIVATE_BALANCE` — not enough tokens for withdraw/transfer.
- `PRIVACY_LEAK` — wallet detected that privacy may be compromised (shape and covered cases still open).

Reused from existing wallet spec:

- `USER_REFUSED_OP` (113) — user rejected in wallet UI.
- `INVALID_REQUEST_PAYLOAD` — malformed actions.
- `API_VERSION_NOT_SUPPORTED`.

## Open questions

1. Should the non-privacy-aware dapp fund/sweep flow have spec-level support (e.g. a session-done signal that triggers the sweep prompt), or stay entirely in wallet UI?
2. Should recipient-not-registered and channel-not-setup be explicit errors, or handled transparently by the wallet auto-setting up channels?
3. Exact shape of the `PRIVACY_LEAK` error and what cases it covers.
