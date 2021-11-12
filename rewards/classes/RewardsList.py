from dotmap import DotMap
from rich.console import Console
from eth_utils.hexadecimal import encode_hex
from eth_abi import encode_abi
from eth_utils.address import to_checksum_address


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

    def increase_user_rewards_source(self, source, user, token, toAdd):
        if not self.sources[source][user][token]:
            self.sources[source][user][token] = 0
        self.sources[source][user][token] += toAdd

    def __repr__(self):
        return self.claims

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

    def to_node_entry(self, user, userData, cycle, index):
        """
        Use abi.encode() to encode data into the hex format used as raw node information in the tree
        This is the value that will be hashed to form the rest of the tree
        """
        nodeEntry = {
            "user": user,
            "tokens": [],
            "cumulativeAmounts": [],
            "cycle": cycle,
            "index": index,
        }
        intAmounts = []
        for tokenAddress, cumulativeAmount in userData.items():
            if cumulativeAmount > 0:
                nodeEntry["tokens"].append(tokenAddress)
                nodeEntry["cumulativeAmounts"].append(str(int(cumulativeAmount)))
                intAmounts.append(int(cumulativeAmount))

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
                    int(nodeEntry["index"]),
                    nodeEntry["user"],
                    int(nodeEntry["cycle"]),
                    nodeEntry["tokens"],
                    intAmounts,
                ),
            )
        )

        # encoder = BadgerTree.at(web3.toChecksumAddress("0x660802Fc641b154aBA66a62137e71f331B6d787A"))

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

        return (nodeEntry, encoded_local)

    def to_merkle_format(self):
        """
        - Sort users into alphabetical order
        - Node entry = [cycle, user, index, token[], cumulativeAmount[]]
        """
        cycle = self.cycle

        nodeEntries = []
        encodedEntries = []
        entries = []

        index = 0

        for user, userData in self.claims.items():
            (nodeEntry, encoded) = self.to_node_entry(user, userData, cycle, index)
            nodeEntries.append(nodeEntry)
            encodedEntries.append(encoded)
            entries.append({"node": nodeEntry, "encoded": encoded})
            index += 1

        return (nodeEntries, encodedEntries, entries)
