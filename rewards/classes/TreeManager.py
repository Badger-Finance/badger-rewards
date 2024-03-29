import json
import time
from typing import List
from typing import Tuple

from eth_account import Account
from eth_utils import to_bytes
from eth_utils.hexadecimal import encode_hex
from hexbytes import HexBytes
from web3.contract import ContractFunction

from config.constants.chain_mappings import CHAIN_IDS
from config.singletons import env_config
from helpers.discord import get_discord_url
from helpers.discord import send_message_to_discord
from helpers.enums import Network
from helpers.web3_utils import get_badger_tree
from logging_utils import logger
from rewards.aws.trees import download_latest_tree
from rewards.aws.trees import download_tree
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.RewardsList import RewardsList
from rewards.explorer import get_explorer_url
from rewards.utils.tx_utils import build_and_send
from rewards.utils.tx_utils import confirm_transaction
from rewards.utils.tx_utils import create_tx_options
from rewards.utils.tx_utils import get_gas_price_of_tx


class TreeManager:
    def __init__(self, chain: str, cycle_account: Account):
        self.chain = chain
        self.w3 = env_config.get_web3(chain)
        self.badger_tree = get_badger_tree(chain)
        self.next_cycle = self.get_current_cycle() + 1
        self.propose_account = cycle_account
        self.approve_account = cycle_account
        self.discord_url = get_discord_url(chain)

    def convert_to_merkle_tree(self, rewardsList: RewardsList, start: int, end: int):
        return rewards_to_merkle_tree(rewardsList, start, end)

    def build_function_and_send(self, account, func) -> str:
        options = create_tx_options(account.address, self.w3, self.chain)
        return build_and_send(func, options, self.w3, account.key)

    def approve_root(self, rewards) -> Tuple[str, bool]:
        logger.info("Approving root")
        return self.manage_root(rewards, self.badger_tree.approveRoot, action="Approve")

    def propose_root(self, rewards):
        logger.info("Proposing root")
        return self.manage_root(rewards, self.badger_tree.proposeRoot, action="Propose")

    def manage_root(self, rewards, contract_function: ContractFunction, action: str):
        root_hash = rewards["rootHash"]
        merkle_root = rewards["merkleTree"]["merkleRoot"]
        start_block = rewards["merkleTree"]["startBlock"]
        end_block = rewards["merkleTree"]["endBlock"]
        root_func = contract_function(
            to_bytes(hexstr=merkle_root),
            to_bytes(hexstr=root_hash),
            int(rewards["merkleTree"]["cycle"]),
            int(start_block),
            int(end_block),
        )

        tx_hash = HexBytes(0)
        try:
            tx_hash = self.build_function_and_send(self.approve_account, func=root_func)
            # Wait 5 seconds before confirming a transaction
            # to make sure the node can see the tx receipt
            time.sleep(5)
            succeeded, msg = confirm_transaction(self.w3, tx_hash, self.chain)
            title = f"**{action} Rewards on {self.chain}**"
            approve_info = f"TX Hash: {tx_hash} \n\n " \
                           f"Root: {merkle_root} \n\n Content Hash: {root_hash} \n\n"
            description = f"Calculated rewards between {start_block} " \
                          f"and {end_block} \n\n {approve_info} "
            logger.info(f"Cycle {action.lower()} : {tx_hash}")

            if succeeded:
                gas_price_of_tx = get_gas_price_of_tx(self.w3, self.chain, tx_hash)
                logger.info(f"got gas price of tx: {gas_price_of_tx}")
                send_message_to_discord(
                    title,
                    description,
                    [
                        {
                            "name": "Completed Transaction",
                            "value": get_explorer_url(self.chain, tx_hash),
                            "inline": True,
                        },
                        {
                            "name": "Gas Cost",
                            "value": (
                                f"${round(get_gas_price_of_tx(self.w3, self.chain, tx_hash), 2)}"
                            ),
                            "inline": True,
                        },
                    ],
                    "Rewards Bot",
                    url=self.discord_url,
                )
            else:
                send_message_to_discord(
                    title,
                    description,
                    [
                        {
                            "name": "Pending Transaction",
                            "value": get_explorer_url(self.chain, tx_hash),
                            "inline": True,
                        }
                    ],
                    "Rewards Bot",
                    url=self.discord_url,
                )
        except Exception as e:
            logger.error(f"Error processing harvest tx: {e}")
            send_message_to_discord(
                f"**FAILED {action} Rewards on {self.chain}**",
                e,
                [],
                "Rewards Bot",
                url=self.discord_url,
            )
            return tx_hash, False
        return tx_hash, True

    def get_current_cycle(self) -> str:
        return self.badger_tree.currentCycle().call()

    def get_claimable_for(self, user: str, tokens: List[str], cumAmounts: List[int]):
        return self.badger_tree.getClaimableFor(user, tokens, cumAmounts).call()

    def get_claimed_for(self, user: str, tokens: List[str]):
        claimed_for_data = self.badger_tree.getClaimedFor(
            self.w3.toChecksumAddress(user), list(tokens)
        ).call()
        return dict(zip(claimed_for_data[0], claimed_for_data[1]))

    def has_pending_root(self) -> bool:
        return self.badger_tree.hasPendingRoot().call()

    def fetch_tree(self, merkle):
        chain_id = CHAIN_IDS[self.chain]
        file_name = f"rewards-{chain_id}-{merkle['contentHash']}.json"
        tree = json.loads(download_tree(file_name, self.chain))
        self.validate_tree(merkle, tree)
        return tree

    def fetch_current_tree(self):
        if env_config.fix_cycle:
            return download_latest_tree(self.chain)
        current_merkle = self.fetch_current_merkle_data()
        logger.info(f"Current Merkle \n {current_merkle}")
        return self.fetch_tree(current_merkle)

    def fetch_pending_tree(self):
        pending_merkle = self.fetch_pending_merkle_data()
        logger.info(f"Pending Merkle \n {pending_merkle}")
        return self.fetch_tree(pending_merkle)

    def validate_tree(self, merkle, tree):
        # Invariant: merkle should have same root as latest
        assert tree["merkleRoot"] == merkle["root"]
        last_update_publish = int(merkle["blockNumber"])
        last_update = int(tree["endBlock"])
        # Arbitrum captures l1 blocks with block.timestamp causing an error
        if self.chain != Network.Arbitrum:
            assert last_update_publish > last_update
        # Ensure file tracks block within 1 day of upload

    def fetch_current_merkle_data(self):
        root = self.badger_tree.merkleRoot().call()
        content_hash = self.badger_tree.merkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(content_hash),
            "lastUpdateTime": self.badger_tree.lastPublishTimestamp().call(),
            "blockNumber": int(self.badger_tree.lastPublishBlockNumber().call()),
        }

    def fetch_pending_merkle_data(self):
        root = self.badger_tree.pendingMerkleRoot().call()
        pending_content_hash = self.badger_tree.pendingMerkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(pending_content_hash),
            "lastUpdateTime": self.badger_tree.lastProposeTimestamp().call(),
            "blockNumber": int(self.badger_tree.lastProposeBlockNumber().call()),
        }

    def last_propose_end_block(self) -> int:
        return self.badger_tree.lastProposeEndBlock().call()

    def last_publish_end_block(self) -> int:
        return self.badger_tree.lastPublishEndBlock().call()

    def last_propose_start_block(self) -> int:
        return self.badger_tree.lastProposeStartBlock().call()

    def matches_pending_hash(self, new_hash: bytes) -> bool:
        new_hash = HexBytes(new_hash)
        pending_hash = HexBytes(self.badger_tree.pendingMerkleContentHash().call())
        return pending_hash.hex() == new_hash.hex()
