![Badger Logo](./images/badger-logo.png)

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

# Testing

Badger Boost calculation: `python -m scripts.rewards.propose_boost`

# Development

### Rewards
In order to deploy on an EVM chain, the following is required

- RPC endpoint for specific chain
- Subgraph for tracking user balances (api subgraph)
- Subgraph for tracking tree distribution events
- Subgraph for tracking tokens
- Gas estimation api for that chain
- Badger Tree + Rewards Logger contracts
- AWS bucket for storing merkle trees and initial empty tree file
