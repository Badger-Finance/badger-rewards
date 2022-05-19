import json
from decimal import Decimal

if __name__ == "__main__":
    boosts = {}
    initial_sum = Decimal(0)
    boosted_sum = Decimal(0)
    max_boost_sum = Decimal(0)
    with open('scripts/badger-boost.json') as f:
        boosts = json.load(f)
    
    for user, boostData in boosts["userData"].items():
        initial_sum += Decimal(boostData["nativeBalance"])
        boosted_sum += Decimal(boostData["nativeBalance"]) * Decimal(boostData["boost"])
        if boostData['boost'] == 3000:
            max_boost_sum += Decimal(boostData["nativeBalance"])

    print(initial_sum)
    print(boosted_sum)
    print(max_boost_sum)
    print(max_boost_sum / initial_sum)
