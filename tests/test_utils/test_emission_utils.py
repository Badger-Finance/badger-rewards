from rewards.utils.emission_utils import (
    fetch_unboosted_vaults,
    get_flat_emission_rate,
)
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from config.constants import addresses
from config.constants.chain_mappings import SETTS
from helpers.enums import Network
from tests.utils import set_env_vars

set_env_vars()


class MockTime:
    def __init__(self):
        pass

    def time(self):
        return 1637086012


def mock_fetch_setts(*args, **kwargs):
    return [
        SETTS[Network.Ethereum]["ren_crv"],
        SETTS[Network.Ethereum]["sbtc_crv"],
        SETTS[Network.Ethereum]["cvx"],
    ]


def test_fetch_unboosted_vaults(mocker):
    mocker.patch("rewards.utils.emission_utils.fetch_setts", mock_fetch_setts)
    mocker.patch(
        "rewards.utils.emission_utils.env_config.get_web3",
        MagicMock(
            return_value=MagicMock(
                eth=MagicMock(
                    get_block=MagicMock(
                        return_value={"timestamp": 100}
                    )
                )
            )
        )
    )
    mocker.patch("rewards.utils.emission_utils.make_contract", MagicMock(
        return_value=MagicMock(
            getAllUnlockSchedulesFor=MagicMock(
                return_value=MagicMock(call=MagicMock(side_effect=[[], [], [
                    [
                        SETTS[Network.Ethereum]["cvx"],
                        addresses.BADGER,
                        1e18,
                        0,
                        200,
                        200
                    ]
                ]])),
            )
        )
    ))
    unboosted_vaults = [
        SETTS[Network.Ethereum]["ren_crv"],
        SETTS[Network.Ethereum]["sbtc_crv"]
    ]
    vaults = fetch_unboosted_vaults(Network.Ethereum, 0)
    assert vaults == unboosted_vaults
