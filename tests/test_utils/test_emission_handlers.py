from config.constants.addresses import XSUSHI
from rewards.classes.RewardsList import RewardsList

from rewards.emission_handlers import bvecvx_lp_handler


def test_bvecvx_lp_handler(mocker):
    mocker.patch(
        "rewards.emission_handlers.sett_snapshot",
        return_value=None
    )
    distribute_func = mocker.patch(
        "rewards.emission_handlers.distribute_rewards_from_total_snapshot",
        return_value=RewardsList()
    )
    bvecvx_lp_handler(123, XSUSHI, "", 123)
    assert distribute_func.called
