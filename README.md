![Badger Logo](./images/badger-logo.png)

### Test coverage:
[![codecov](https://codecov.io/gh/Badger-Finance/badger-rewards/branch/development/graph/badge.svg?token=0JIZAA720B)](https://codecov.io/gh/Badger-Finance/badger-rewards)
# Badger Rewards

Badger Rewards hosts scripts directly related to the Badger Rewards system, including:
-   calculating Badger Boost
-   proposing roots for rewards distribution
-   approving roots for rewards distribution

Visit our [GitBook](https://app.gitbook.com/@badger-finance/s/badger-tech/) for more detailed documentation.

# Current deployed bots

### Boost Bot
```
Chain: Ethereum
Cadence: Every 10m
```

## Rewards deployment
In order to deploy on an EVM chain, the following is required

- RPC endpoint for specific chain
- Subgraph for tracking user balances (api subgraph)
- Subgraph for tracking tree distribution events
- Subgraph for tracking tokens
- Gas estimation api for that chain
- Badger Tree + Rewards Logger contracts
- AWS bucket for storing merkle trees and initial empty tree file


# Development

### Releasing a feature
When not sure if feature can break something, consider using feature flags functionality
to disable code that is causing troubles

First, add new feature flag to `FeatureFlags.FLAGS` dictionary:
```python
class FeatureFlags:
    FLAGS: Dict[str, bool] = {
        NEW_FLAG: True
    }
```
Then use new flag to wrap potentially dangerous code:
```python
from rewards.feature_flags import flags

def some_func():
    if flags.flag_enabled(NEW_FLAG):
        new_functionality()
    else:
        old_functionality()
```

After succesful release consider removing `NEW_FLAG` and the code also
