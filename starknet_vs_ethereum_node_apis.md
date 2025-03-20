# General

This document provides information to developers who wish to work with StarkNet's node RPC API and
are familiar with Ethereum's RPC API. The document focuses on existing APIs, specifically targeting
distributed application developers.

As a general rule, the APIs are similar in naming, semantics and conventions. We generally follow
the same methods used in Ethereum's node API and make changes where the technology requires it to
maintain consistency.

Below you can find a summary of the changes, whether cross-cutting or method-specific. We also
provide a mapping of methods.

We currently compare Ethereum 1.0 API, as defined [here](https://github.com/ethereum/execution-apis),
 and [StarkNet's API](https://github.com/starkware-libs/starknet-specs/blob/master/api/starknet_api_openrpc.json).

Familiarity with Ethereum and [StarkNet](https://starkware.co/product/starknet/) is assumed herein.

## Cross-Cutting Changes

Some differences are more fundamental and manifest in different API methods.

**Block and Transaction objects:** Block and transaction objects have a somewhat different structure
 compared to Ethereum. These changes are mainly due to different network mechanics, e.g., no proof
 of work in StarkNet.

**Block Tags:** In some cases, the API refers to a block using relative tags that point to a block
in a specific position in the chain or state (latest, earliest, pending). Where applicable,
StarkNet allows referring only to the latest block, using the `latest` tag.

## Naming Conventions

Unless otherwise noted, the method names used are the same method names with a different prefix.
The `eth` prefix is replaced with `starknet`.

## Types

The fundamental data type in StarkNet is a field element. As a corollary, all resulting blocks and
transactions' hashes are also field elements. When referring to a block/transaction type or an
address, StarkNet uses a field element, not a 256-bit number.

The field element type in StarkNet is based on the field in the underlying Cairo VM.
In other words, a value x of a field element type is an integer in the range of `0≤x<P`. `P` is currently defined as `2^251+17*2^192+1`

# Mapping of Methods

We list below the methods in Ethereum's API and their corresponding StarkNet methods.

|Ethereum Method|StarkNet Method|Differences From Ethereum|
|---------------|---------------|-------------------------|
|eth_blockNumber|starknet_blockNumber|Will return only the block number |
|eth_chainId|starknet_chainId| |
|eth_getBlockByNumber|starknet_getBlockByNumber|<ul><li> Doesn’t have the include transactions input.</li><li> The result key is "result".</li></ul> |
|eth_getBlockTransactionCountByHash|starknet_getBlockTransactionCountByHash|<ul><li> Supports also "latest" block tag as input</li><li> The result is always an integer</li><li> The response key is "result".</li><li> May return an error for invalid block hash.</li></ul> |
|eth_getBlockTransactionCountByNumber|starknet_getBlockTransactionCountByNumber|<ul><li> Block number input is given as a decimal integer.</li><li> The result key is "result".</li><li> May return an error for invalid block number.</li></ul> |
|eth_getTransactionByBlockHashAndIndex|starknet_getTransactionByBlockHashAndIndex|<li> The Index is given as a decimal integer. |
|eth_getTransactionByBlockNumberAndIndex|starknet_getTransactionByBlockNumberAndIndex|<li> The index is given as a decimal integer. |
|eth_pendingTransactions|starknet_pendingTransactions|<ul><li> The result key is "result".</li><li> Will not return market fee parameters.</li></ul> |
|eth_getBlockByHash|starknet_getBlockByHash|<ul><li> Doesn’t have the include transactions input.</li><li> The result key is "result".</li></ul> |
|eth_protocolVersion|starknet_protocolVersion|
|eth_syncing|starknet_syncing|<li> The result will not include known and pulled states
|eth_getStorageAt|starknet_getStorageAt|<ul><li> Accepts a block hash instead of a block number</li><li> The result key is "result".</li><li> The result type is a field element.</li><li> Will return errors for invalid contract or storage keys.</li></ul> |
|eth_getTransactionByHash|starknet_getTransactionByHash|<ul><li> Input key is "transaction_hash".</li><li> The result key is "result".</li><li> Will not return null.</li><li> Will return an error for an invalid transaction hash.</li></ul> |
|eth_getTransactionReceipt|starknet_getTransactionReceipt|<ul><li> Input key is "transaction_hash".</li><li> The result key is "result".</li><li> Will not return null.</li><li> Will return an error for an invalid transaction hash.</li></ul> |
|eth_getCode|starknet_getCode|<ul><li> The input key is "contract_address".</li><li> Does not accept a block number.</li><li> Will return byte code (field elements) and ABI.</li><li> Will return an error for an invalid contract address.</li></ul> |
|eth_call|starknet_call|<ul><li> Input transaction is different.</li><li> Input block designated by hash.</li><li> Will return errors for invalid contract address| message selector| call data| or general error.</li></ul> |
