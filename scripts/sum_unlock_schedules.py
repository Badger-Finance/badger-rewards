from brownie import *
from rewards.classes.Schedule import Schedule
from scripts.systems.badger_system import connect_badger

from helpers.constants import DFD
from rich.console import Console

console = Console()


def main():
    badger = connect_badger()
    sett = "0x8a8ffec8f4a0c8c9585da95d9d97e8cd6de273de"
    badger.print_logger_unlock_schedules(sett, "ibbtc/wbtc slp")
