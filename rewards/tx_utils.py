from decimal import Decimal
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.web3_utils import make_contract
from helpers.constants import EMISSIONS_CONTRACTS
from hexbytes import HexBytes
import logging
import time
import requests
from web3 import Web3, exceptions
from typing import Tuple
from helpers.enums import Network, BotType

logger = logging.getLogger("tx-utils")


def get_gas_price_of_tx(
    web3: Web3,
    chain: str,
    tx_hash: HexBytes,
    timeout: int = 60,
) -> Decimal:
    """Gets the actual amount of gas used by the transaction and converts
    it from gwei to USD value for monitoring.

    Args:
        web3 (Web3): web3 node instance
        gas_oracle (contract): web3 contract for chainlink gas unit / usd oracle
        tx_hash (HexBytes): tx id of target transaction
        chain (str): chain of tx (valid: eth, poly)

    Returns:
        Decimal: USD value of gas used in tx
    """
    tx, tx_receipt = get_transaction(
        web3, tx_hash, timeout, chain, bot_type=BotType.Cycle
    )
    logger.info(f"tx: {tx_receipt}")
    total_gas_used = Decimal(tx_receipt.get("gasUsed", 0))
    logger.info(f"gas used: {total_gas_used}")
    gas_oracle = make_contract(
        EMISSIONS_CONTRACTS[chain]["GasOracle"], abi_name="ChainlinkOracle", chain=chain
    )

    if chain == Network.Ethereum:
        gas_price_base = Decimal(tx_receipt.get("effectiveGasPrice", 0) / 10 ** 18)
    elif chain in [Network.Polygon, Network.Arbitrum]:
        gas_price_base = Decimal(tx.get("gasPrice", 0) / 10 ** 18)

    gas_usd = Decimal(
        gas_oracle.latestAnswer().call() / 10 ** gas_oracle.decimals().call()
    )

    gas_price_of_tx = total_gas_used * gas_price_base * gas_usd
    logger.info(f"gas price of tx: {gas_price_of_tx}")

    return gas_price_of_tx


def get_latest_base_fee(web3: Web3, default=int(100e9)):  # default to 100 gwei
    latest = web3.eth.get_block("latest")
    raw_base_fee = latest.get("baseFeePerGas", hex(default))
    if type(raw_base_fee) == str and raw_base_fee.startswith("0x"):
        base_fee = int(raw_base_fee, 0)
    else:
        base_fee = int(raw_base_fee)
    return base_fee


def get_effective_gas_price(web3: Web3, chain: str = Network.Ethereum) -> int:
    # TODO: Currently using max fee (per gas) that can be used for this tx. Maybe use base + priority (for average).
    if chain == Network.Ethereum:
        base_fee = get_latest_base_fee(web3)
        logger.info(f"latest base fee: {base_fee}")

        priority_fee = get_priority_fee(web3)
        logger.info(f"avg priority fee: {priority_fee}")
        # max fee aka gas price enough to get included in next 6 blocks
        gas_price = 2 * base_fee + priority_fee
    elif chain == Network.Polygon:
        response = requests.get("https://gasstation-mainnet.matic.network").json()
        gas_price = web3.toWei(int(response.get("fast") * 1.1), "gwei")
    elif chain == Network.Arbitrum:
        gas_price = web3.eth.gas_price * 1.1
    return gas_price


def get_priority_fee(
    web3: Web3,
    num_blocks: str = "0x4",
    percentile: int = 70,
    default_reward: int = int(10e9),
) -> int:
    """Calculates priority fee looking at current block - num_blocks historic
    priority fees at the given percentile and taking the average.

    Args:
        web3 (Web3): Web3 object
        num_blocks (str, optional): Number of historic blocks to look at in hex form (no leading 0s). Defaults to "0x4".
        percentiles (int, optional): Percentile of transactions in blocks to use to analyze fees. Defaults to 70.
        default_reward (int, optional): If call fails, what default reward to use in gwei. Defaults to 10e9.

    Returns:
        int: [description]
    """
    gas_data = web3.eth.fee_history(num_blocks, "latest", [percentile])
    rewards = gas_data.get("reward", [[default_reward]])
    priority_fee = int(sum([r[0] for r in rewards]) / len(rewards))

    logger.info(f"piority fee: {priority_fee}")
    return priority_fee


def get_transaction(
    web3: Web3,
    tx_hash: HexBytes,
    timeout: int,
    chain: str,
    tries: int = 5,
    bot_type: BotType = BotType.Cycle,
) -> Tuple[dict, dict]:
    attempt = 0
    error = None
    discord_url = get_discord_url(chain, bot_type)
    while attempt < tries:
        try:
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            tx = web3.eth.get_transaction(tx_hash)
            msg = f"Transaction {tx_hash} succeeded!"
            send_message_to_discord(
                "Transaction Success", msg, [], "Rewards Bot", discord_url
            )
            return tx, receipt
        except Exception as e:
            msg = f"Error waiting for {tx_hash}. Error: {e}. \n Retrying..."
            attempt += 1
            error = e
            logger.error(msg)
            send_message_to_discord(
                "Transaction Error", msg, [], "Rewards Bot", discord_url
            )
            time.sleep(5)

    msg = f"Error waiting for {tx_hash} after {tries} tries"
    send_message_to_discord("Transaction Error", msg, [], "Rewards Bot", discord_url)
    raise error


def confirm_transaction(
    web3: Web3, tx_hash: HexBytes, chain: str, timeout: int = 60
) -> Tuple[bool, str]:
    """Waits for transaction to appear within a given timeframe or before a given block (if specified), and then times out.

    Args:
        web3 (Web3): Web3 instance
        tx_hash (HexBytes): Transaction hash to identify transaction to wait on.
        timeout (int, optional): Timeout in seconds. Defaults to 60.
        max_block (int, optional): Max block number to wait until. Defaults to None.

    Returns:
        bool: True if transaction was confirmed, False otherwise.
        msg: Log message.
    """
    logger.info(f"tx_hash before confirm: {tx_hash}")

    try:
        get_transaction(web3, tx_hash, timeout, chain)
        msg = f"Transaction {tx_hash} succeeded!"
        logger.info(msg)
        return True, msg
    except exceptions.TimeExhausted:
        msg = f"Transaction {tx_hash} timed out, not included in block yet."
        return False, msg
    except Exception as e:
        msg = f"Error waiting for {tx_hash}. Error: {e}."
        logger.error(msg)
        return False, msg
