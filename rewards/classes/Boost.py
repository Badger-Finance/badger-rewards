from dataclasses import dataclass
from typing import Dict, Optional
from decimal import Decimal


@dataclass
class BoostBalances:
    native: Dict[str, Decimal]
    non_native: Dict[str, Decimal]
    bvecvx: Optional[Dict[str, Decimal]]
    nfts: Optional[Dict[str, Decimal]]

