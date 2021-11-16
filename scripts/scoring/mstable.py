import json

from scoring.scoring_utils import get_nft_owners

from config.singletons import env_config
from rewards.explorer import fetch_block_by_timestamp, get_block_by_timestamp
from rewards.snapshot.chain_snapshot import chain_snapshot

if __name__ == "__main__":
    w3 = env_config.get_web3()

    boost_limit = 300
    boost_file = json.load(open("badger-boosts.json"))["userData"]
    boost_users = []
    for addr, boost_info in boost_file.items():
        if boost_info["boost"] >= 20:
            boost_users.append(w3.toChecksumAddress(addr))

    print(len(boost_users))
    with open("mstable.json", "w") as fp:
        json.dump(boost_users, fp)
