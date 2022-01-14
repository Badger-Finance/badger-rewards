from rewards.rewards_checker import token_diff_table


def test_token_diff_table():
    table_item = token_diff_table(
        name="bBADGER",
        before=100,
        after=200,
        decimals=1
    )
    assert table_item == (100, [
        'bBADGER',
        '10.000000000000000000',
        '20.000000000000000000',
        '10.000000000000000000'
    ])
