from decimal import Decimal
from unittest import TestCase

import pytest

from helpers.constants import BADGER
from helpers.enums import Network
from rewards.snapshot.nft_snapshot import nft_snapshot_usd


@pytest.fixture()
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.snapshot.nft_snapshot.fetch_nfts", mock_fetch_nfts)
    monkeypatch.setattr(
        "rewards.snapshot.nft_snapshot.get_nft_weight", mock_get_nft_score
    )

    monkeypatch.setattr(
        "rewards.classes.Snapshot.fetch_token_prices", mock_fetch_token_prices
    )
    monkeypatch.setattr(
        "rewards.classes.Snapshot.send_message_to_discord", mock_send_message_to_discord
    )


def mock_get_nft_score(chain: Network, nft_address: str, nft_id: int):
    nft_scores = {
        "0xe1e546e25A5eD890DFf8b8D005537c0d373497F8-1": 200,
        "0xe4605d46Fd0B3f8329d936a8b258D69276cBa264-97": 10,
    }
    return nft_scores.get(f"{nft_address}-{nft_id}", 0)


def mock_fetch_nfts(chain: str, block: int):

    jersey_nft = {"address": "0xe1e546e25A5eD890DFf8b8D005537c0d373497F8", "id": 1}
    honeypot_1 = {"address": "0xe4605d46Fd0B3f8329d936a8b258D69276cBa264", "id": 97}
    fake_nft = {"address": "0xE592427A0AEce92De3Edee1F18E0157C05861564", "id": 100}
    return {
        "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": [jersey_nft, honeypot_1],
        "0xbC641f6C6957096857358Cc70df3623715A2ae45": [honeypot_1],
        "0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0": [jersey_nft],
        "0x320C24c9d6a2B2337F883c51d857D92f9aBFF8DD": [fake_nft],
    }


def mock_fetch_token_prices():
    return {BADGER: 10}


def mock_send_message_to_discord(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    return True


def test_nft_snapshot_usd(mock_fns):
    chain = Network.Ethereum
    expected_snapshot_usd = {
        "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": Decimal(210 * 10),
        "0xbC641f6C6957096857358Cc70df3623715A2ae45": Decimal(10 * 10),
        "0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0": Decimal(200 * 10),
        "0x320C24c9d6a2B2337F883c51d857D92f9aBFF8DD": Decimal(0),
    }
    snapshot_usd = nft_snapshot_usd(chain, block=0)
    TestCase().assertDictEqual(d1=snapshot_usd, d2=expected_snapshot_usd)
