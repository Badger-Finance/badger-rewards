from functools import lru_cache
from typing import Dict

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from config.constants.addresses import ETH_BADGER_TREE
from config.constants.chain_mappings import EMISSIONS_CONTRACTS

from config.singletons import env_config
from helpers.discord import send_error_to_discord
from helpers.enums import Network
from helpers.web3_utils import make_token
from rewards.aws.helpers import dynamodb, get_metadata_table, get_snapshot_table
from rewards.snapshot.claims_snapshot import claims_snapshot
from subgraph.queries.setts import last_synced_block


@lru_cache
def get_claimable_metadata(chain: Network, block: int) -> Dict:
    kce = Key("chain").eq(chain) & Key("startBlock").between(0, block)
    table = dynamodb.Table(get_metadata_table(env_config.production))
    try:
        output = table.query(
            IndexName="IndexMetadataChainAndStartBlock",
            KeyConditionExpression=kce,
            ScanIndexForward=False,
            Limit=1,
        )
    except ClientError as e:
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Client Error",
            chain,
        )
        raise e
    else:
        return output["Items"][0]


def get_latest_claimable_metadata(chain: Network):
    return get_claimable_metadata(chain, block=last_synced_block(chain))


def get_claimable_balances(chain: Network, chain_start_block: str) -> Dict[str, float]:
    table = dynamodb.Table(get_snapshot_table(env_config.production))
    try:
        kce = Key("chainStartBlock").eq(chain_start_block)
        response = table.query(KeyConditionExpression=kce)
        data = response["Items"]
        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=kce,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            data.extend(response["Items"])
    except ClientError as e:
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Client Error",
            chain,
        )
        raise e
    else:
        return data


def get_latest_claimable_snapshot(chain: Network):
    metadata = get_latest_claimable_metadata(chain)
    return get_claimable_balances(chain, metadata["chainStartBlock"])


def get_claimable_data(chain: Network, block: int):
    metadata = get_claimable_metadata(chain, block)
    return get_claimable_balances(chain, metadata["chainStartBlock"])

def get_claimable_rewards_data(chain: Network, block: int):
    snapshots = claims_snapshot(chain, block)
    deficits = {}
    for token, snapshot in snapshots.items():
        token_contract = make_token(token, chain)
        tree_balance = token_contract.balanceOf(EMISSIONS_CONTRACTS[chain]["BadgerTree"])
        claimable_balance = float(snapshot.total_balance())
        deficits[token] = tree_balance - claimable_balance
    return deficits
        