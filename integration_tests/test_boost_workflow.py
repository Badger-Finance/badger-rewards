import logging
from collections import Counter
from decimal import Decimal

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.boost import add_user_data
from rewards.boost.calc_boost import badger_boost
from tests.test_utils.cycle_utils import mock_upload_boosts
from tests.utils import (
    mock_boosts,
    mock_send_code_block_to_discord,
    mock_send_message_to_discord_prod,
    set_env_vars,
)

logger = logging.getLogger("test-boost")

set_env_vars()


def mock_claims_snapshot_usd(*args, **kwargs):
    native = Counter()
    non_native = Counter()

    return native, non_native


def raise_exc():
    raise Exception()


def test_boost_workflow(monkeypatch, mocker):
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_prod
    )
    monkeypatch.setattr(
        "rewards.boost.calc_boost.send_code_block_to_discord",
        mock_send_code_block_to_discord,
    )
    monkeypatch.setattr(
        "rewards.aws.boost.download_boosts", lambda *args, **kwargs: mock_boosts
    )
    monkeypatch.setattr(
        "rewards.boost.boost_utils.claims_snapshot_usd", mock_claims_snapshot_usd
    )
    monkeypatch.setattr("rewards.aws.boost.upload_boosts", mock_upload_boosts)
    monkeypatch.setattr(
        "badger_api.claimable.get_claimable_metadata",
        lambda *args, **kwargs:
        {'chain': 'ethereum', 'startBlock': Decimal('14217430'), 'endBlock': Decimal('14217974'),
         'cycle': Decimal('4348'), 'chainStartBlock': 'ethereum_14217430'}
    )
    current_block = env_config.get_web3().eth.block_number
    user_data = badger_boost(current_block, Network.Ethereum)
    # mock upload boosts has asserts baked in to check nothing Decimal,
    # and saves file to test serialization
    add_user_data(user_data, Network.Ethereum)
