"""Tests for the Starknet MCP server.

Unit tests (no network):
  pytest tests/test_server.py -m "not integration"

Integration tests (live mainnet RPC):
  pytest tests/test_server.py -m integration
  pytest tests/test_server.py -m integration --network testnet-sepolia
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import server
from server import parse_block_id, rpc, state


def _result(raw: str) -> object:
    """Parse a JSON-RPC response string and assert there is no error."""
    data = json.loads(raw)
    assert "error" not in data, f"RPC returned error: {data['error']}"
    return data["result"]


# ── Fixtures ──────────────────────────────────────────────────────────────────

# A stable finalized mainnet block that always has transactions.
STABLE_BLOCK_NUMBER = 500_000
STABLE_BLOCK_ID = json.dumps({"block_number": STABLE_BLOCK_NUMBER})

# ETH token contract — always deployed on mainnet at this address.
ETH_CONTRACT = "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"

# STRK token contract.
STRK_CONTRACT = "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
# STRK class hash (fetched via starknet_getClassHashAt on latest)
STRK_CLASS_HASH = "0x4ad3c1dc8413453db314497945b6903e1c766495a1e60492d44da9c2a986e4b"

# Storage key for the "total_supply" slot in the ETH contract (Pedersen of "ERC20_total_supply").
ETH_TOTAL_SUPPLY_KEY = "0x110e2f729c9c2b988559994a3daccd838cf52faf88e18101373e67dd061455a"


@pytest.fixture(scope="module")
async def stable_block():
    """Fetch a known finalized block and cache it for the module."""
    raw = await rpc("starknet_getBlockWithTxHashes", [parse_block_id(STABLE_BLOCK_ID)])
    result = _result(raw)
    return result


@pytest.fixture(scope="module")
async def known_tx_hash(stable_block):
    """Return the first transaction hash from the stable block."""
    txs = stable_block.get("transactions", [])
    if not txs:
        pytest.skip(f"Block {STABLE_BLOCK_NUMBER} has no transactions")
    return txs[0]


@pytest.fixture(scope="module")
async def stable_block_hash(stable_block):
    return stable_block["block_hash"]


# ── Unit tests: parse_block_id ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "block_id, expected",
    [
        ("latest", "latest"),
        ("pending", "pending"),
        ("pre_confirmed", "pre_confirmed"),
        ("0", {"block_number": 0}),
        ("1234", {"block_number": 1234}),
        ("999999", {"block_number": 999999}),
        ('{"block_number": 99}', {"block_number": 99}),
        ('{"block_hash": "0xabc"}', {"block_hash": "0xabc"}),
        (
            '{"block_hash": "0x047c3637b57c2b079b93c61539950c17e868a28f46cdef28f88521067f21e943"}',
            {"block_hash": "0x047c3637b57c2b079b93c61539950c17e868a28f46cdef28f88521067f21e943"},
        ),
        (
            "0x047c3637b57c2b079b93c61539950c17e868a28f46cdef28f88521067f21e943",
            {"block_hash": "0x047c3637b57c2b079b93c61539950c17e868a28f46cdef28f88521067f21e943"},
        ),
    ],
)
def test_parse_block_id(block_id, expected):
    assert parse_block_id(block_id) == expected


@pytest.mark.parametrize("block_id", ["", "not-a-block", "latestt"])
def test_parse_block_id_rejects_invalid(block_id):
    with pytest.raises(ValueError):
        parse_block_id(block_id)


async def test_set_network_url():
    original = state["url"]
    custom = "http://localhost:9545/rpc/v0_10"
    try:
        await server.set_network(custom)
        assert state["url"] == custom
    finally:
        state["url"] = original


# ── Integration tests: live mainnet RPC ───────────────────────────────────────


@pytest.mark.integration
async def test_starknet_specVersion():
    result = _result(await rpc("starknet_specVersion", []))
    assert isinstance(result, str)
    # Semver format: "major.minor.patch"
    parts = result.split(".")
    assert len(parts) == 3, f"Expected semver, got: {result}"


@pytest.mark.integration
async def test_starknet_blockNumber():
    result = _result(await rpc("starknet_blockNumber", []))
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.integration
async def test_starknet_blockHashAndNumber():
    result = _result(await rpc("starknet_blockHashAndNumber", []))
    assert "block_hash" in result
    assert "block_number" in result
    assert result["block_hash"].startswith("0x")
    assert isinstance(result["block_number"], int)


@pytest.mark.integration
async def test_starknet_chainId():
    result = _result(await rpc("starknet_chainId", []))
    assert isinstance(result, str)
    assert result.startswith("0x")
    # Mainnet chain ID
    assert result == "0x534e5f4d41494e"


@pytest.mark.integration
async def test_starknet_syncing():
    result = _result(await rpc("starknet_syncing", []))
    # Either False (synced) or a sync status object
    assert result is False or isinstance(result, dict)


@pytest.mark.integration
async def test_starknet_getBlockWithTxHashes_latest():
    result = _result(await rpc("starknet_getBlockWithTxHashes", ["latest"]))
    assert "block_number" in result
    assert "block_hash" in result
    assert "transactions" in result
    assert isinstance(result["transactions"], list)


@pytest.mark.integration
async def test_starknet_getBlockWithTxHashes_by_number(stable_block):
    assert stable_block["block_number"] == STABLE_BLOCK_NUMBER


@pytest.mark.integration
async def test_starknet_getBlockWithTxHashes_by_hash(stable_block_hash):
    result = _result(
        await rpc(
            "starknet_getBlockWithTxHashes",
            [{"block_hash": stable_block_hash}],
        )
    )
    assert result["block_hash"] == stable_block_hash


@pytest.mark.integration
async def test_starknet_getBlockWithTxs():
    result = _result(await rpc("starknet_getBlockWithTxs", ["latest"]))
    assert "transactions" in result
    if result["transactions"]:
        tx = result["transactions"][0]
        assert "transaction_hash" in tx
        assert "type" in tx


@pytest.mark.integration
async def test_starknet_getBlockWithReceipts():
    result = _result(await rpc("starknet_getBlockWithReceipts", ["latest"]))
    assert "transactions" in result
    if result["transactions"]:
        entry = result["transactions"][0]
        assert "transaction" in entry
        assert "receipt" in entry


@pytest.mark.integration
async def test_starknet_getBlockTransactionCount():
    result = _result(
        await rpc(
            "starknet_getBlockTransactionCount",
            [parse_block_id(STABLE_BLOCK_ID)],
        )
    )
    assert isinstance(result, int)
    assert result >= 0


@pytest.mark.integration
async def test_starknet_getTransactionByHash(known_tx_hash):
    result = _result(await rpc("starknet_getTransactionByHash", [known_tx_hash]))
    assert result["transaction_hash"] == known_tx_hash
    assert "type" in result


@pytest.mark.integration
async def test_starknet_getTransactionByBlockIdAndIndex():
    result = _result(
        await rpc(
            "starknet_getTransactionByBlockIdAndIndex",
            [parse_block_id(STABLE_BLOCK_ID), 0],
        )
    )
    assert "transaction_hash" in result
    assert "type" in result


@pytest.mark.integration
async def test_starknet_getTransactionStatus(known_tx_hash):
    result = _result(await rpc("starknet_getTransactionStatus", [known_tx_hash]))
    assert "finality_status" in result
    assert result["finality_status"] in ("ACCEPTED_ON_L1", "ACCEPTED_ON_L2")


@pytest.mark.integration
async def test_starknet_getTransactionReceipt(known_tx_hash):
    result = _result(await rpc("starknet_getTransactionReceipt", [known_tx_hash]))
    assert "transaction_hash" in result
    assert "execution_status" in result
    assert "events" in result


@pytest.mark.integration
async def test_starknet_getStateUpdate():
    result = _result(
        await rpc("starknet_getStateUpdate", [parse_block_id(STABLE_BLOCK_ID)])
    )
    assert "block_hash" in result
    assert "state_diff" in result


@pytest.mark.integration
async def test_starknet_getStorageAt():
    # Read ETH contract total_supply storage slot
    result = _result(
        await rpc(
            "starknet_getStorageAt",
            [ETH_CONTRACT, ETH_TOTAL_SUPPLY_KEY, "latest"],
        )
    )
    assert isinstance(result, str)
    assert result.startswith("0x")


@pytest.mark.integration
async def test_starknet_getNonce():
    result = _result(
        await rpc("starknet_getNonce", ["latest", ETH_CONTRACT])
    )
    assert isinstance(result, str)
    assert result.startswith("0x")


@pytest.mark.integration
async def test_starknet_getClass():
    result = _result(await rpc("starknet_getClass", ["latest", STRK_CLASS_HASH]))
    # Either a Sierra class (has "sierra_program") or legacy (has "entry_points_by_type")
    assert "sierra_program" in result or "entry_points_by_type" in result


@pytest.mark.integration
async def test_starknet_getClassHashAt():
    result = _result(await rpc("starknet_getClassHashAt", ["latest", STRK_CONTRACT]))
    assert result == STRK_CLASS_HASH


@pytest.mark.integration
async def test_starknet_getClassAt():
    result = _result(await rpc("starknet_getClassAt", ["latest", STRK_CONTRACT]))
    assert "sierra_program" in result or "entry_points_by_type" in result


@pytest.mark.integration
async def test_starknet_call():
    # Call ETH token's name() function
    # entry_point_selector for "name" = keccak("name") truncated
    name_selector = "0x361458367e696363fbcc70777d07ebbd2394e89fd0adcaf147faccd1d294d60"
    result = _result(
        await rpc(
            "starknet_call",
            [
                {
                    "contract_address": ETH_CONTRACT,
                    "entry_point_selector": name_selector,
                    "calldata": [],
                },
                "latest",
            ],
        )
    )
    assert isinstance(result, list)


@pytest.mark.integration
async def test_starknet_getEvents():
    result = _result(
        await rpc(
            "starknet_getEvents",
            [
                {
                    "from_block": {"block_number": STABLE_BLOCK_NUMBER},
                    "to_block": {"block_number": STABLE_BLOCK_NUMBER},
                    "chunk_size": 10,
                }
            ],
        )
    )
    assert "events" in result
    assert isinstance(result["events"], list)


@pytest.mark.integration
async def test_starknet_traceTransaction(known_tx_hash):
    result = _result(await rpc("starknet_traceTransaction", [known_tx_hash]))
    # All traces have a type and execution_resources field.
    assert "type" in result, f"Missing 'type' in trace: {list(result.keys())}"
    assert "execution_resources" in result, f"Missing 'execution_resources' in trace"


@pytest.mark.integration
async def test_starknet_traceBlockTransactions():
    result = _result(
        await rpc(
            "starknet_traceBlockTransactions",
            [parse_block_id(STABLE_BLOCK_ID)],
        )
    )
    assert isinstance(result, list)
    if result:
        assert "transaction_hash" in result[0]
        assert "trace_root" in result[0]


@pytest.mark.integration
async def test_starknet_getStorageProof():
    # Storage proofs are only supported for recent blocks — use latest.
    result = _result(
        await rpc(
            "starknet_getStorageProof",
            {
                "block_id": "latest",
                "contract_addresses": [ETH_CONTRACT],
            },
        )
    )
    assert "contracts_proof" in result or "global_roots" in result
