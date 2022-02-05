from dataclasses import dataclass
from typing import Dict
from rewards.boost.boost_utils import BoostMetadata
from decimal import Decimal


    
@dataclass
class BoostBalances:
    native: Dict[str, Decimal]
    non_native: Dict[str, Decimal]
    bvecvx: Dict[str, Decimal]
    nfts: Dict[str, Decimal]