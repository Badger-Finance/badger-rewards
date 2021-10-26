from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot


def print_claimable(chain):
    snapshots = claims_snapshot(chain)
    for token, snapshot in snapshots.items():
        print(token, snapshot.total_balance())


if __name__ == "__main__":
    print_claimable(Network.Arbitrum)
