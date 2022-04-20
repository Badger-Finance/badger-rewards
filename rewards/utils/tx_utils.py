import logging
import time
from decimal import Decimal
from typing import Optional, Tuple

from eth_typing import HexStr
from web3 import Web3, exceptions

from config.constants import GAS_BUFFER
from config.constants.chain_mappings import DECIMAL_MAPPING, EMISSIONS_CONTRACTS
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import Abi, BotType, Network
from helpers.http_client import http_client
from helpers.web3_utils import make_contract

logger = logging.getLogger("tx-utils")


def get_gas_price_of_tx(
    web3: Web3,
    chain: str,
    tx_hash: HexStr,
    timeout: int = 60,
    retries_on_failure: Optional[int] = 5,
) -> Optional[Decimal]:
    """Gets the actual amount of gas used by the transaction and converts
    it from gwei to USD value for monitoring.

    Args:
        web3 (Web3): web3 node instance
        tx_hash (HexStr): tx id of target transaction
        chain (str): chain of tx (valid: eth, poly)
        timeout(int): time to wait on tx fetch failure
        retries_on_failure(int): retry amount of times if tx fetching fails
    Returns:
        Decimal: USD value of gas used in tx
    """
    tx, tx_receipt = get_transaction(
        web3, tx_hash, timeout, chain, bot_type=BotType.Cycle, tries=retries_on_failure
    )
    logger.info(f"tx: {tx_receipt}")
    total_gas_used = Decimal(tx_receipt.get("gasUsed", 0))
    logger.info(f"gas used: {total_gas_used}")
    gas_oracle = make_contract(
        EMISSIONS_CONTRACTS[chain]["GasOracle"],
        abi_name=Abi.ChainlinkOracle,
        chain=chain,
    )

    if chain == Network.Ethereum:
        gas_price_base = Decimal(
            tx_receipt.get("effectiveGasPrice", 0) / DECIMAL_MAPPING[chain]
        )
    elif chain in [Network.Polygon, Network.Arbitrum, Network.Fantom]:
        gas_price_base = Decimal(tx.get("gasPrice", 0) / DECIMAL_MAPPING[chain])
    else:
        return
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
    # TODO: Currently using max fee (per gas) that can be used for this tx.
    # TODO: Maybe use base + priority (for average).
    gas_price = None
    if chain == Network.Ethereum:
        base_fee = get_latest_base_fee(web3)
        logger.info(f"latest base fee: {base_fee}")

        priority_fee = get_priority_fee(web3)
        logger.info(f"avg priority fee: {priority_fee}")
        # max fee aka gas price enough to get included in next 6 blocks
        gas_price = 2 * base_fee + priority_fee
    elif chain == Network.Polygon:
        json = http_client.get("https://gasstation-mainnet.matic.network")
        if json:
            gas_price = web3.toWei(int(json.get("fast") * 1.1), "gwei")
    elif chain in [Network.Arbitrum, Network.Fantom]:
        gas_price = int(web3.eth.gas_price * GAS_BUFFER)
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
        num_blocks (str, optional): Number of historic blocks
            to look at in hex form (no leading 0s). Defaults to "0x4".
        percentile (int, optional): Percentile of transactions in blocks
            to use to analyze fees. Defaults to 70.
        default_reward (int, optional): If call fails, what default reward
            to use in gwei. Defaults to 10e9.

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
    tx_hash: HexStr,
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
    web3: Web3,
    tx_hash: HexStr,
    chain: str,
    timeout: int = 60,
    retries_on_failure: Optional[int] = 5,
) -> Tuple[bool, str]:
    """Waits for transaction to appear within a given timeframe
    or before a given block (if specified), and then times out.

    Args:
        web3 (Web3): Web3 instance
        tx_hash (HexStr): Transaction hash to identify transaction to wait on.
        chain (str): chain of tx (valid: eth, poly)
        timeout (int, optional): Timeout in seconds. Defaults to 60.
        retries_on_failure(int): retry amount of times if tx fetching fails
    Returns:
        bool: True if transaction was confirmed, False otherwise.
        msg: Log message.
    """
    logger.info(f"tx_hash before confirm: {tx_hash}")

    try:
        get_transaction(web3, tx_hash, timeout, chain, tries=retries_on_failure)
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


def create_tx_options(address, w3, chain):
    options = {
        "nonce": w3.eth.get_transaction_count(address),
        "from": address,
    }
    if chain == Network.Ethereum:
        options["maxPriorityFeePerGas"] = get_priority_fee(w3)
        options["maxFeePerGas"] = get_effective_gas_price(w3, chain)
        options["gas"] = 200000
    elif chain == Network.Arbitrum:
        options["gas"] = 3000000
    options["gasPrice"] = get_effective_gas_price(w3, chain)
    return options


def build_and_send(func, options, w3, pkey):
    tx = func.buildTransaction(options)
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=pkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
    return tx_hash
