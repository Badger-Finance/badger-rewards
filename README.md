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

1. `cp .env.example .env` to copy the environment variables file to a local file
2. Update the `.env` file with relevant information
3. run `brownie run scripts/rewards/<SCRIPT NAME>.py` to test the script you'd like.