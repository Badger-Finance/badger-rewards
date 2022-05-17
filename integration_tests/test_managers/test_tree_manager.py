import pytest
from helpers.enums import Network
from config.constants import addresses
from tests.test_utils.cycle_utils import mock_tree_manager


@pytest.fixture
def tree_manager(chain, cycle_account):
    tree_manager = mock_tree_manager(chain, cycle_account)
    return tree_manager


@pytest.mark.parametrize(
    "tree_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_matches_pending_hash(tree_manager):
    pending_hash = tree_manager.badger_tree.pendingMerkleContentHash().call()
    assert tree_manager.matches_pending_hash(pending_hash)

    random_hash = "0xb8ed7da2062b6bdf6f20bcdb4ab35538592216ac70a4bfe986af748603debfd8"
    assert not tree_manager.matches_pending_hash(random_hash)


@pytest.mark.parametrize(
    "tree_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_get_claimed_for(tree_manager):
    user = "0xEE9F84Af6a8251Eb5ffDe38c5F056bc72d3b3DD0"
    tokens = [
        addresses.BADGER,
        addresses.BVECVX
    ]
    claimed_for_tokens = tree_manager.get_claimed_for(
        user,
        tokens
    )
    for token in tokens:
        assert claimed_for_tokens[token] > 0
