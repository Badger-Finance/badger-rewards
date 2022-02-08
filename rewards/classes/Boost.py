from dataclasses import dataclass, field
from typing import Dict, Optional
from decimal import Decimal

@dataclass
class BoostBalances:
    native: Dict[str, Decimal]
    non_native: Dict[str, Decimal]
    bvecvx: Dict[str, Decimal] = field(default_factory=lambda: {})
    nfts: Dict[str, Decimal] = field(default_factory=lambda: {})



