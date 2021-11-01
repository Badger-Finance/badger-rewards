from scripts.rewards.fix_cycle.fix_cycle import fix_cycle
import json

if __name__ == "__main__":
    fix_cycle("polygon", json.load(open("badger-tree-137.json")))