export WEB3_INFURA_PROJECT_ID=$(aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-west-1:342684350154:secret:boost-bot/infura-id-zb9i9o | jq -r ".SecretString" | jq -r ".INFURA_ID")
brownie run scripts/rewards/propose_boost.py --network=mainnet
