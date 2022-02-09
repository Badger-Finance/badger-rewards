from web3 import Web3


class RoleRegistry:
    def __init__(self):
        self.roles = {}

    def add_role(self, name):
        encoded = Web3.keccak(text=name).hex()
        self.roles[name] = encoded

ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
MAX_UINT_256 = str(int(2 ** 256 - 1))
EMPTY_BYTES_32 = "0x0000000000000000000000000000000000000000000000000000000000000000"

DEFAULT_ADMIN_ROLE = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)
# Approved Contract Roles
APPROVED_STAKER_ROLE = Web3.keccak(text="APPROVED_STAKER_ROLE").hex()
APPROVED_SETT_ROLE = Web3.keccak(text="APPROVED_SETT_ROLE").hex()
APPROVED_STRATEGY_ROLE = Web3.keccak(text="APPROVED_STRATEGY_ROLE").hex()

PAUSER_ROLE = Web3.keccak(text="PAUSER_ROLE").hex()
UNPAUSER_ROLE = Web3.keccak(text="UNPAUSER_ROLE").hex()
GUARDIAN_ROLE = Web3.keccak(text="GUARDIAN_ROLE").hex()

# BadgerTree Roles
ROOT_UPDATER_ROLE = Web3.keccak(text="ROOT_UPDATER_ROLE").hex()
ROOT_PROPOSER_ROLE = Web3.keccak(text="ROOT_PROPOSER_ROLE").hex()
ROOT_VALIDATOR_ROLE = Web3.keccak(text="ROOT_VALIDATOR_ROLE").hex()

# UnlockSchedule Roles
TOKEN_LOCKER_ROLE = Web3.keccak(text="TOKEN_LOCKER_ROLE").hex()

# Keeper Roles
KEEPER_ROLE = Web3.keccak(text="KEEPER_ROLE").hex()
EARNER_ROLE = Web3.keccak(text="EARNER_ROLE").hex()

# External Harvester Roles
SWAPPER_ROLE = Web3.keccak(text="SWAPPER_ROLE").hex()
DISTRIBUTOR_ROLE = Web3.keccak(text="DISTRIBUTOR_ROLE").hex()

APPROVED_ACCOUNT_ROLE = Web3.keccak(text="APPROVED_ACCOUNT_ROLE").hex()

role_registry = RoleRegistry()

role_registry.add_role("APPROVED_STAKER_ROLE")
role_registry.add_role("APPROVED_SETT_ROLE")
role_registry.add_role("APPROVED_STRATEGY_ROLE")

role_registry.add_role("PAUSER_ROLE")
role_registry.add_role("UNPAUSER_ROLE")
role_registry.add_role("GUARDIAN_ROLE")

role_registry.add_role("ROOT_UPDATER_ROLE")
role_registry.add_role("ROOT_PROPOSER_ROLE")
role_registry.add_role("ROOT_VALIDATOR_ROLE")

role_registry.add_role("TOKEN_LOCKER_ROLE")

role_registry.add_role("KEEPER_ROLE")
role_registry.add_role("EARNER_ROLE")

role_registry.add_role("SWAPPER_ROLE")
role_registry.add_role("DISTRIBUTOR_ROLE")

role_registry.add_role("APPROVED_ACCOUNT_ROLE")
