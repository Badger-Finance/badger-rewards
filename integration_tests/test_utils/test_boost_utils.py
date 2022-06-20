from rewards.boost.boost_utils import get_bvecvx_lp_ratio


def test_get_bvecvx_lp_ratio():
    ratio = get_bvecvx_lp_ratio()
    assert 0 < ratio < 1
