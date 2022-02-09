from helpers.enums import BotType, BucketType, Environment, Network

MONITORING_SECRET_NAMES = {
    Environment.Production: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/eth/prod-discord-url",
            BotType.Boost: "boost-bot/eth/prod-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/prod-discord-url",
            BotType.Boost: "boost-bot/polygon/prod-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/arbitrum/prod-discord-url",
            BotType.Boost: "boost-bot/arbitrum/prod-discord-url",
        },
    },
    Environment.Staging: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/eth/staging-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/polygon/staging-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/arbitrum/staging-discord-url",
        },
    },
    Environment.Test: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
    },
}

S3_BUCKETS = {
    BucketType.Merkle: {
        Environment.Staging: "badger-staging-merkle-proofs",
        Environment.Production: "badger-merkle-proofs",
    }
}
