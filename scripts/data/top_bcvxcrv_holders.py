from helpers.enums import Network
from itertools import islice
from rewards.snapshot.chain_snapshot import sett_snapshot
from config.constants import addresses
import csv
from rewards.snapshot.custom_snapshots import badger_snapshot_usd

from subgraph.queries.setts import last_synced_block

top_number = 120
chain = Network.Ethereum
block = last_synced_block(chain)
bcvxcrv = sett_snapshot(chain, block, addresses.BCVXCRV).convert_to_usd(chain).balances
top_bcvxcrv = dict(sorted(bcvxcrv.items(), key=lambda i: i[1], reverse=True))

top_bcvxcrv = dict(islice(top_bcvxcrv.items(), top_number))
badger_snapshot = badger_snapshot_usd(chain, block)

with open("bcvxcrv_data.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["addr", "bcvxcrv_usd", "badger_holdings_usd"])
    for addr, value in top_bcvxcrv.items():
        badger_amount = badger_snapshot.get(addr, 0)
        writer.writerow([addr, round(value,2), round(badger_amount,2)])


