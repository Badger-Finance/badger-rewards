from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional


@dataclass
class BoostBalances:
    native: Dict[str, Decimal]
    non_native: Dict[str, Decimal]
    bvecvx: Dict[str, Decimal] = field(default_factory=lambda: {})
    nfts: Dict[str, Decimal] = field(default_factory=lambda: {})
