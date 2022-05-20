from helpers.digg_utils import DiggUtils


def test_digg_utils_shares_to_frag(mocker):
    mocker.patch("helpers.digg_utils.make_contract")
    utils = DiggUtils()
    shares_per_fragment = 100
    utils.shares_per_fragment = shares_per_fragment
    shares = 123
    assert utils.shares_to_fragments(shares) == shares / shares_per_fragment


def test_digg_utils_fragment_to_shares(mocker):
    mocker.patch("helpers.digg_utils.make_contract")
    utils = DiggUtils()
    shares_per_fragment = 100
    utils.shares_per_fragment = shares_per_fragment
    fragments = 123
    assert utils.fragments_to_shares(fragments) == fragments * shares_per_fragment


def test_digg_utils_shares_to_frag_zero(mocker):
    mocker.patch("helpers.digg_utils.make_contract")
    utils = DiggUtils()
    assert utils.shares_to_fragments(0) == 0


def test_digg_utils_fragment_to_shares_zero(mocker):
    mocker.patch("helpers.digg_utils.make_contract")
    utils = DiggUtils()
    assert utils.fragments_to_shares(0) == 0
