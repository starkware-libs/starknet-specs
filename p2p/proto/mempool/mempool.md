# Starknet Mempool Protocol

## Overview
The goal of the mempool p2p protocol is to allow mempools to share transactions they receive through RPC.
This will make it so that once a user submits a transaction to one mempool it will appear across all mempools.

## Gossipsub
The protocol is based on the [Gossipsub](https://docs.libp2p.io/concepts/pubsub/overview/) protocol, V1.1

The topic for this protocol is: `"/starknet/mempool_transaction_propagation/0.1.0"`.

We use Gossipsub to publish transactions once they reach the node through RPC.

Once a node receives a transaction, it should verify it against the current state by running
`validate` before continuing its propagation to other nodes.
This is to prevent giving scale for a DDoS attack.

Our choice of using Gossipsub might change in the future if we encounter performance issues with it.

## Transaction
The object that we're passing is a [MempoolTransaction](./transaction.proto). A few notes about it:
* It contains support only for V3 transactions. Transaction prior to V3 can't be a part of a mempool
because they don't have the required fields to  enter the fee market
* It doesn't contain a variant for L1Handler transactions. The reason is that mempools can learn
about existing L1Handler transactions by simply looking at L1
* In Declare, it contains the SIERRA of the class being declared. The reason it doesn't contain the
CASM of the class is that the mempool should validate that the CASM came from the compilation of a
SIERRA class and not from an unsafe class.

## No sync
We've decided to not implement a protocol for syncing on existing transactions in the mempool.

The reason for that is that we're aiming for a very low block time (1-2 seconds) and a very high TPS (1000+).
The combination of these means that most transactions will be either included in a block or evicted within a few seconds after their arrival.

This means that a new mempool will have most of the transactions that an older mempool would have within a few seconds after it starts listening for new transactions.
