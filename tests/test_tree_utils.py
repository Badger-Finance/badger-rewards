import os
import pytest
from brownie import accounts, Contract, web3
from decimal import Decimal
from hexbytes import HexBytes
from web3 import contract


from rewards.tree_utils import get_last_proposed_cycle
from rewards.classes.TreeManager import TreeManager
from tests.utils import test_address, test_key
