from scripts.rewards.utils.approve_rewards import approve_rewards
import time
from rich.console import Console

console = Console()

if __name__ == "__main__":
    while True:
        try:
            approve_rewards("eth")
        except Exception as e:
            console.print("[red]Error[/red]", e)
        finally:
            time.sleep(10 * 60)
