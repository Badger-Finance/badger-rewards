## AURA Snapshot Distribution

`scripts/aura.py` is a script to determine the holdings of users in the below contracts for a fair distribution:
- Rari Fuse
- bveCVX / CVX LP Vault
- Unclaimed Earnings

The script pulls these balances and produces a JSON file in the below format:
```
{
    contract_address: {
        user_address: percent_of_bvecvx_in_contract
    }
}
```

To generate the file you'd perform the below actions:

```
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> python -m scripts.aura
```

This will generate the JSON file `aura.json` in the root of the project.  You can then determine the distribution of the allocated rewards to the contract by user by multiplying the total allocated rewards * user percentage of holdings.  For example:

```
rari_fuse_total_aura = 200_000
lp_total_aura = 150_000
unclaimed_total_aura = 5_000_000

aura_data = {
    rari: {
        user_1: 50,
        user_2: 20,
        user_3: 18,
        user_4: 12
    },
    ...
}

user_1_aura = aura_data[rari][user_1] / 100 * rari_fuse_total_aura
...
```

In this case, User 1 would receive 100k AURA from their rari fuse holdings, User 2 getting 40k, and so on.
