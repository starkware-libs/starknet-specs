# Starknet Consensus Protocol

This is the network spec for Starknet's implementation of Tendermint. The consensus network is built
atop [libp2p](https://libp2p.io/). It uses a pubsub model with separate topics for votes and
proposals.

Validators are encouraged to be in the Mempool and Sync networks in addition to the consensus
network.

- Mempool network allows validators to learn of new transactions.
- Sync network is needed by a node to catch up if it falls behind the network's consensus.

Validators are expected to listen on the network before the height they are scheduled to join at is
reached.

# [Votes][VoteLink]

This topic uses a broadcast model.

- topic name: consensus_votes

Votes are atomic messages, meaning each network message corresponds to a single logical consensus
vote.

In order to ensure all validators receive enough votes to progress, validators are expected to
periodically resend their latest prevote and precommit. This is aimed to bring us closer aligned
with the Partially Synchronous Model, which is difficult to simply assume in a real network.

# Proposals

This topic uses a broadcast model.

- topic name: consensus_proposals

Starknet sends proposals as streams of network messages. This enables:

1. Proposals to be larger than a single message.
2. Higher utilization, as Validators can begin re-executing while the Proposer is still building.

Tendermint, though, views Proposals as a single logical event. To that end, the primary consensus
based messages are:

1. [ProposalInit][ProposalInitLink] - the fields of the Tendermint proposal which can be known
   before the proposer completes block building.
2. [ProposalFin][ProposalFinLink] - the proposed value ID and the proposer's signature on the block
   proposed.

## Order of messages

The standard order for a Proposal:

1. [ProposalInit][ProposalInitLink] - once (includes all block metadata)
1. [TransactionBatch][TransactionBatchLink] - multiple (for non-empty blocks)
1. [ProposalFin][ProposalFinLink] - once

### Executed Transaction Count

The `executed_transaction_count` field in [ProposalFin][ProposalFinLink] is used to allow for
increased parallelism between the proposer and the validators. Specifically, the proposer can
broadcast batches of transactions before it has executed them. The Proposer may time out before
executing all of the transactions sent and so it sends the number of transactions it did execute.
This may require validators to roll back transactions if they executed transactions sent which the
proposer didn't execute.

### Proposal Commitment

In Starknet, validators vote on an execution of a Proposal, not on an identifier of the values
proposed. The primary reason for this is that Starknet is optimizing for the e2e latency between:

1. End user submits a TX
2. The effect of that TX is widely visible; consensus has been reached on the StateDiff including
   it.

The `proposal_commitment` included in [ProposalFin][ProposalFinLink] uniquely identifies the proposed block and can help debug disagreements between nodes.

### Self Justifying Reproposals

A validator can become locked on a value `v` after seeing `2f+1` prevotes in favor of it; resending
`v` when it is this validator's turn to propose and not voting in favor of other values proposed.
While `2f+1` nodes prevoted in favor of `v` we do not know how many saw these prevotes. Therefore we
want a node to justify when it sets `valid_round` by sending a list of prevotes which prove this
lock is valid.

#### Eventual Delivery of Votes

Tendermint assumes that all messages arrive after GST. While resending votes takes us part of the
way, it is not enough under byzantine conditions where it is still possible for nodes to get [stuck](https://github.com/informalsystems/malachite/discussions/380).

Due to memory limits, nodes do not hold all equivocating votes as the paper implies. Instead they
decide from among the set of equivocating votes some subset to utilize and some subset to ignore. We
do not define at the protocol level how to decide these sets when receiving individual votes. When
votes are received as part of a quorum certificate, the votes in the certificate should take
precedence over those with which they equivocate votes.

#### Validations on Reproposals

Some fields in a proposal do not require validations once consensus has been reached on them. This
extends to a prevote quorum. So a validator which receives a reproposal `v`, for which it knows the
prevote quorum supporting `v`, need not re-validate these fields.

### Empty Proposals

A proposer may not be able to offer a valid proposal. If so, the height can be agreed to be empty.
Order of messages (no [TransactionBatch][TransactionBatchLink] messages are sent):

1. [ProposalInit][ProposalInitLink]
2. [ProposalFin][ProposalFinLink]

# [Streaming][StreamMessageLink]

We define here a generic streaming protocol which is used for proposals.

`message_id` - field which defines the order of messages (0 based).

`content` - the application level information (encoded as bytes).

`fin` - signals the last message on the stream.

- If a receiver sees a message with `message_id` greater than that of the fin's
  `message_id` it may either ignore such messages or reject the stream.

`stream_id` - identifier of the stream to which the message belongs.

## Stream ID

Field which identifies a stream of messages.

- The primary requirement is that a given sender never reuse the `stream_id`.
- Receivers identify streams based on (sender_id, `stream_id`), so distinct senders need not
  coordinate IDs.
- Applications are not expected to derive meaning from the `stream_id`. The primary reason for being
  generic is to put information which may be useful for humans when debugging.
- This field should be small to avoid unnecessary overhead.

# TODO

1. Add fork ID.
1. Define a signature scheme for consensus messages.
1. Known proposal - [ProposalFin][ProposalFinLink] before content.
1. Specify levels of finality for each field in ProposalCommitment

---

[VoteLink]: consensus.proto#L20
[ProposalPartLink]: consensus.proto#L100
[ProposalInitLink]: consensus.proto#L47
[ProposalFinLink]: consensus.proto#L88
[TransactionBatchLink]: consensus.proto#L64
[StreamMessageLink]: consensus.proto#L38
