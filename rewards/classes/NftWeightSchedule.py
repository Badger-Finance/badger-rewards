from dataclasses import dataclass

from helpers.time_utils import to_utc_date


@dataclass
class NFTWeightSchedule:
    addr: str
    nft_id: int
    weight: int
    timestamp: int

    def __repr__(self):
        return (
            f"NftWeightSchedule(addr={self.addr},"
            f"id={self.nft_id},"
            f"weight={self.weight},"
            f"startTime={to_utc_date(self.timestamp)},"
        )
