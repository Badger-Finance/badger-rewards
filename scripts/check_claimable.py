from helpers.enums import Network


def print_claimable(chain):
    snapshots = claims_snapshot(chain)
    for token, snapshot in snapshots.items():
        print(token, snapshot.total_balance())


if __name__ == "__main__":
    print_claimable(Network.Arbitrum)
