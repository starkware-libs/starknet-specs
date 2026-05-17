# Starknet Sync Protocols

## Terminology
`Request` - The message that is sent in order to request data from another node.

`Response` - The message that is sent in response to a `Request` message and contains the requested data.

`Querying peer` - The peer that sent the `Request` message.

`Replying peer` - The peer that received the `Request` message.

`Session` - All the messages related to responding to a `Request`. Including both the `Request`
message and all the `Response` messages. This term is used to distinguish between `Response`
messages from one `Request` to another.

## Protocols Briefing
The following table describes the different protocols in Starknet, the name that should be used in
negotiation, and the protobuf messages related to the protocol.
| Protocol | Name (for negotiation) | Request Message | Response Message |
| ------------ | -------------- | -------------- | -------------- |
| Headers | /starknet/<chain_id>/sync/headers/0.1.0-rc.0 | [BlockHeadersRequest](./header.proto) | [BlockHeadersResponse](./header.proto) |
| StateDiffs | /starknet/<chain_id>/sync/state_diffs/0.1.0-rc.0 | [StateDiffsRequest](./state.proto) | [StateDiffsResponse](./state.proto) |
| Classes | /starknet/<chain_id>/sync/classes/0.1.0-rc.0 | [ClassesRequest](./class.proto) | [ClassesResponse](./class.proto) |
| Transactions | /starknet/<chain_id>/sync/transactions/0.1.0-rc.0 | [TransactionsRequest](./transaction.proto) | [TransactionsResponse](./transaction.proto) |
| Events | /starknet/<chain_id>/sync/events/0.1.0-rc.0 | [EventsRequest](./event.proto) | [EventsResponse](./event.proto) |
| Kademlia (for discovery) | /starknet/<chain_id>/sync/kad/1.0.0 |

In addition, nodes should also support the `Identify` protocol, who's name for negotiation is
`/ipfs/id/1.0.0`

## Overview
In each Starknet protocol (except for Kademlia and Identify), one peer sends a single request
message and the other peer responds with multiple response messages

The request is always a range of blocks and the responses are data related to those blocks.

This allows the querying peer to process data (e.g., calculate hashes) before it downloaded all the
data that the replying peer sent in the session.

The data sent is always a `oneof` of messages containing data and a [Fin](#fin).

### Partitioning data into blocks
Except for the [headers](#headers) protocol, the partition of data into blocks does not appear in
the data itself.

This partition can be done based on the data in the header.

For each protocol, in the header, there's a commitment on the data given by this protocol.
The commitment is made of a hash and the number of elements

The commitment is included inside the block hash. Meaning that it can be validated once we
downloaded the header.

The length field can be used to determine in each protocol when does the data of one block stop and
the data of the next block after it begins.

### Length Prefix
Each response message is prefixed with the amount of bytes that the encoded message contains.

The length is written as a [varint](https://protobuf.dev/programming-guides/encoding/#varints)

The request message is not prefixed with length. The querying peer should close its writer end once
it sends the request message (it's the only message it should send in the session). The replying peer
should read bytes until it reaches EOF and thus it doesn't need to know the length before reading
the message

### Limits
- Each message must be less than 1MB, except for the [Class](../class.proto) message which is allowed
to be up to 4MB.
- TBD limits on the amount of total messages/bytes in a single session
- TBD timeout for a session
- TBD timeout between two messages

### Optional fields
In `proto3`, each field that's a nested message is optional, and the `optional` keyword does nothing
for that field (See this [issue](https://github.com/protocolbuffers/protobuf/issues/249)).

We want to mark nested fields as required, so every field that is not marked as `optional` is
considered required, even if it's nested.

If a peer sends a message with a missing required field, they are considered malicious.

### Iteration
The request message in each protocol contains an [Iteration](./common.proto). 

The Iteration message defines an ordered range of blocks.

The Iteration message has the following fields:
- **start**: The first block that we request, by hash or by number
- **direction**: Decides whether the blocks we send after the starting block are the blocks after it
or the blocks before it
- **limit**: The amount of blocks requested
- **step**: Given a step `i`, the responder will return every i'th block it sees until it reached `limit` blocks.

For example. If the request has the values:
- **start**: 10
- **direction**: Backward
- **limit**: 3
- **step**: 3

Then the blocks we'll receive will be blocks no. 10, 7, 4

### Fin
The [Fin](../common.proto) message is an empty message that signals the end of a protocol.
After sending all the data, the replying peer sends a Fin message.
If a replying peer sends any additional messages after sending a fin message, they are considered
malicious and the connection with them should be dropped.

### Missing Data
We currently assume that if a peer has some of the data for a block then it has all the data for
that block.

If the replying peer doesn't have all the data for all the blocks in the request, it should send
all the data for the blocks it has according to the order of the iteration and stop and send Fin
when it encountered the first missing block (even if it's the first block).

### Pre-0.13.2 blocks
Starting from Starknet v0.13.2, the block hash covers all the data related to the block that a peer
can download from another peer

The fields that are not in the block hash of blocks before v0.13.2 are:
* State diff commitment and length
* Receipt commitment
* L1 data availability mode
* Gas and data gas prices
* In event commitment, the emitting transaction

This means that a peer cannot download those blocks from an untrusted peer, because
the replying peer can change the value of those fields and the signed block hash won't change.

In order to solve this issue, we will add a file with all the hashes of blocks from all public
Starknet chains, where every hash is calculated with the v0.13.2 formula.

## Protocols Breakdown
### Headers
The Headers protocol is used to download block headers and signatures.

Its name for negotiation is `/starknet/headers/0.1.0-rc.0`

Each single message is a fin or a [SignedBlockHeader](./header.proto)

A header is comprised of:
* block hash
* hash of the parent block
* block number
* metadata for the block (timestamp, sequencer address, protocol version, gas prices)
* Commitments on the data of each of the other protocols. Each commitment is comprised of length and
hash. For more details see the [block hash description](https://docs.google.com/document/d/1EIlHskVJEyztS8eXRyPzd8cZwGuPcIKR5xUAIawzryk/edit)

There's a single message for each block. That's because we assume that there will never be a header
that's bigger than the [message size limit](#limits), even when including all signatures for this
header.

### Transactions and Receipts
The transactions protocol is used to download the transactions and receipts in a range of blocks.

Its name for negotiation is `/starknet/transactions/0.1.0-rc.0`

Each single message is either a fin, or a [TransactionWithReceipt](./transaction.proto)
(A pair of [TransactionInBlock](./transaction.proto) and [Receipt](./receipt.proto))

Each transaction represents a Starknet transaction that's already part of the Starknet chain.
For more detail on the different transaction types, their content and their hash calculation see [here](https://docs.starknet.io/documentation/architecture_and_concepts/Network_Architecture/transactions/).

The main differences between [TransactionInBlock](./transaction.proto) and a transaction that is pending insertion ([ConsensusTransaction](../consensus/consensus.proto) or [MempoolTransaction](../mempool/transaction.proto))
are:
* TransactionInBlock supports old transaction versions, including the deprecated deploy transaction.
* TransactionInBlock's declare doesn't contain the sierra class. It just contains the class hash.


A receipt is comprised of
* The hash of the transaction this receipt belongs to
* The actual fee paid for this transaction and the price unit used for the payment
* The messages to l1 this transaction generated.
* The execution resources this transaction took. Comprised of Cairo resources and data availability
resources
* The revert reason as a string if this transaction was reverted. If the `revert_reason` field is
missing, it means that this transaction was successful

The transactions and receipts need to be sent according to the transaction execution order.

The commitment of the transactions in the header is comprised of the number of transactions and
their merkle root.

In order to verify the transactions, the node needs to calculate their hash and compare it to the
transactions merkle root in the block header.

The same is true for receipts. They also have a commitment in the header.

The number can be used to delimiter between the transactions and receipts of each block. 

In order to avoid potential DDoS, the querying peer should reject the connection and declare the
replying peer malicious once it sent more transactions with receipts than the sum of transaction
amounts in the headers of the requested blocks.

### Events
The Events protocol is used to download the events emitted in a range of blocks.

Its name for negotiation is `/starknet/events/0.1.0-rc.0`

Each single message is a fin or an [Event](./event.proto)

Each event contains
* The hash of the transaction that emitted this event
* The address of the contract that emitted this event.
* The keys and data of this event.

The commitment of the events in the header is comprised of the number of events and
their merkle root.

In order to verify the events, the node needs to calculate their hash and compare it to the
events merkle root in the block header.

The number can be used to delimiter between the events of each block, and the transaction index field
of each event is used to delimiter between the events of each transaction within a block.

In order to avoid potential DDoS, the querying peer should reject the connection and declare the
replying peer malicious once it sent more events than the sum of event amounts in the headers of the
requested blocks.

### State Diff
The state diff protocol is used to download the state diffs created by a range of blocks.
It can be used to avoid running the transactions for computing the state diff.

Its name for negotiation is `/starknet/state_diffs/0.1.0-rc.0`

In order to verify the state diff, the node needs to calculate its hash and compare it to the
`state_diff_commitment` field in the block header. The structure of the hash is detailed [here](https://community.starknet.io/t/introducing-p2p-authentication-and-mismatch-resolution-in-v0-12-2/97993)

#### Message structure
Each single message is either a fin, a [ContractDiff](./state.proto) or a [DeclaredClass](./state.proto).

A ContractDiff represents all the changes made for a given contract. This includes:
* Storage diffs - Represented by the `values` field.
* Nonce updates - Represented by the `nonce` field if present.
* Deployed contracts - Represented by the `class_hash` field if present. If it's present it means
that this contract was deployed or replaced in this block.

A DeclaredClass represents a declared class. If the class is Cairo1 then the `compiled_class_hash`
field will be present

There's no guarantee on what ordering will the messages have for a single block's state diff.
The only constraint is that each `ContractDiff` can't be empty, i.e., one of the following fields have
value:
* `nonce`
* `class_hash`
* `values`

#### Length
As we've seen in other protocols like [Transactions](#transactions and receipts), The node needs to know the
amount of data to expect in order to reject malicious peers trying to DDoS the node.

In order to do that, the node needs to look at the block header at the field `state_diff_length`.
This field is equal to
`num_storage_diffs + num_nonce_updates + num_deployed_contracts + num_declared_classes`

Then, whenever the node receives a [StateDiffResponse](./state.proto), it needs to add a number to
a counter and declare the peer malicious if the counter becomes bigger than `state_diff_length`:
* For DeclaredClass, the counter should increase by 1.
* For ContractDiff, the counter should increase by the length of the field `values`,
and by 1 if the field `class_hash` is present, and by 1 if the field `nonce` is present.

### Classes
The classes protocol is used to download the classes declared in a range of blocks.

Its name for negotiation is `/starknet/classes/0.1.0-rc.0`

Each single message is a fin or a [Class](../class.proto). For more information on classes, see
[here](https://docs.starknet.io/documentation/architecture_and_concepts/Smart_Contracts/contract-classes/)

You should use the [state diff protocol](#state-diff) before using this protocol.
The reason is that the class hashes and amount of declared classes per block are part of the
`state_diff_commitment` in the header, and these values are needed to
1. Validate the results of the classes protocol.
2. Delimiter between the classes of each block.
3. Reject a replying peer DDoSing us if it sent more classes than the amount of declared classes in
the block range.

The fact that each class is a single message and each message is up to 4MB gives us a protection
from DDoS the same way other protocols gain protection with a length field.
