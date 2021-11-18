import json
from typing import Any, Dict, List, Tuple

from dotmap import DotMap
from eth_abi import encode_abi
from eth_utils.address import to_checksum_address
from eth_utils.hexadecimal import encode_hex
from rich.console import Console

from badger_api.requests import fetch_token
from helpers.constants import DIGG
from helpers.digg_utils import digg_utils

console = Console()


class RewardsList:
    def __init__(self, cycle: int = 0) -> None:
        self.claims = DotMap()
        self.tokens = DotMap()
        self.totals = DotMap()
        self.cycle = cycle
        self.metadata = DotMap()
        self.sources = DotMap()
        self.sourceMetadata = DotMap()

    def __repr__(self):
        return self.claims

    def __str__(self):
        log_obj = {
            "claims": self.claims.toDict(),
            "tokens": self.tokens.toDict(),
            "totals": self.totals.toDict(),
            "cycle": self.cycle,
            "metadata": self.metadata.toDict(),
            "sources": self.sources.toDict(),
            "sourcesMetadata": self.sourceMetadata.toDict(),
        }
        return json.dumps(log_obj, indent=4)

    def increase_user_rewards_source(self, source, user, token, toAdd):
        if not self.sources[source][user][token]:
            self.sources[source][user][token] = 0
        self.sources[source][user][token] += toAdd

    def totals_info(self, chain: str) -> str:
        info = []
        for token, amount in self.totals.items():
            token_info = fetch_token(chain, token)
            name = token_info.get("name", "")
            decimals = token_info.get("decimals", 18)
            if token == DIGG:
                amount = digg_utils.shares_to_fragments(amount)

            info.append(f"{name}: {round(amount/pow(10,decimals), 5)}")
        return "\n".join(info)

    def track_user_metadata_source(self, source, user, metadata):
        if not self.sourceMetadata[source][user][metadata]:
            self.sourceMetadata[source][user][metadata] = DotMap()
        self.sourceMetadata[source][user][metadata] = metadata

    def user_rewards_sanity_check(self):
        """
        Check to make sure that no duplicate tokens have been added
        """
        tokens = {}
        for token in self.totals:
            assert (
                token.lower() not in self.totals
            ), f"Duplicate token found when adding rewards: {token}"
            assert token == to_checksum_address(
                token
            ), f"Token {token} is not checksummed"
            tokens[token.lower()] = True

    def decrease_user_rewards(self, user, token, to_decrease):
        if user in self.claims and token in self.claims[user]:
            self.claims[user][token] -= to_decrease

        if token in self.totals:
            self.totals[token] -= to_decrease
            if self.totals[token] == 0 and self.totals[to_checksum_address(token)] > 0:
                del self.totals[token]

    def increase_user_rewards(self, user, token, toAdd):
        if toAdd < 0:
            print("NEGATIVE to ADD")
            toAdd = 0

        """
        If user has rewards, increase. If not, set their rewards to this initial value
        """
        # TODO: Update these to checksum at source rather than in this function
        user = to_checksum_address(user)
        token = to_checksum_address(token)
        if user in self.claims and token in self.claims[user]:
            self.claims[user][token] += toAdd
        else:
            self.claims[user][token] = toAdd

        if token in self.totals:
            self.totals[token] += toAdd
        else:
            self.totals[token] = toAdd

        self.user_rewards_sanity_check()

    def hasToken(self, token):
        if self.tokens[token]:
            return self.tokens[token]
        else:
            return False

    def getTokenRewards(self, user, token):
        if self.claims[user][token]:
            return self.claims[user][token]
        else:
            return 0

    def to_node_entry(
        self, user, user_data, cycle, index
    ) -> Tuple[Dict[str, Any], str]:
        """
        Use abi.encode() to encode data into the hex format used as raw node information in the tree
        This is the value that will be hashed to form the rest of the tree
        """
        node_entry = {
            "user": user,
            "tokens": [],
            "cumulativeAmounts": [],
            "cycle": cycle,
            "index": index,
        }
        int_amounts = []
        for tokenAddress, cumulativeAmount in user_data.items():
            if cumulativeAmount > 0:
                node_entry["tokens"].append(tokenAddress)
                node_entry["cumulativeAmounts"].append(str(int(cumulativeAmount)))
                int_amounts.append(int(cumulativeAmount))

        # console.print(
        #     "Encoding Node entry...",
        #     {
        #         "index": int(nodeEntry["index"]),
        #         "account": nodeEntry["user"],
        #         "cycle": int(nodeEntry["cycle"]),
        #         "tokens": nodeEntry["tokens"],
        #         "cumulativeAmounts": nodeEntry["cumulativeAmounts"],
        #         "(integer encoded)": intAmounts,
        #     }
        # )

        encoded_local = encode_hex(
            encode_abi(
                ["uint", "address", "uint", "address[]", "uint[]"],
                (
                    int(node_entry["index"]),
                    node_entry["user"],
                    int(node_entry["cycle"]),
                    node_entry["tokens"],
                    int_amounts,
                ),
            )
        )

        # encoder = BadgerTree.at(
        #     web3.toChecksumAddress("0x660802Fc641b154aBA66a62137e71f331B6d787A")
        # )

        # console.print("nodeEntry", nodeEntry)
        # console.print("encoded_local", encoded_local)

        # ===== Verify encoding on-chain =====
        # encoded_chain = encoder.encodeClaim(
        #     nodeEntry["tokens"],
        #     nodeEntry["cumulativeAmounts"],
        #     nodeEntry["user"],
        #     nodeEntry["index"],
        #     nodeEntry["cycle"],
        # )[0]

        # console.print("encoded_onchain", encoded_chain)
        # assert encoded_local == encoded_chain

        return node_entry, encoded_local

    def to_merkle_format(self) -> Tuple[List[Dict], List[str], List[Dict[str, Any]]]:
        """
        - Sort users into alphabetical order
        - Node entry = [cycle, user, index, token[], cumulativeAmount[]]
        """
        cycle = self.cycle

        node_entries = []
        encoded_entries = []
        entries = []

        index = 0
        self.claims = dict(sorted(self.claims.items()))
        for user, user_data in self.claims.items():
            (node_entry, encoded) = self.to_node_entry(user, user_data, cycle, index)
            node_entries.append(node_entry)
            encoded_entries.append(encoded)
            entries.append({"node": node_entry, "encoded": encoded})
            index += 1

        return node_entries, encoded_entries, entries
