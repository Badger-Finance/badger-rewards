import time

from rich.console import Console

from helpers.enums import Network
from scripts.rewards.eth.approve_eth import approve_rewards
from config.singletons import env_config

console = Console()

if __name__ == "__main__":
    kube = env_config.kube
    while True:
        try:
            approve_rewards(Network.Ethereum, kube)
        except Exception as e:
            console.print("[red]Error[/red]", e)
        finally:
            # Make sure that we run this often, we don't want boost to get out of date
            time.sleep(60 * 5)
