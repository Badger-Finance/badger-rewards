#!/bin/bash
echo "[default]\nregion=us-west-1\noutput=json" > ~/.aws/config
echo "[profile sa]\nrole_arn=arn:aws:iam::342684350154:role/boost-bot" > ~/.aws/credentials
export AWS_PROFILE=sa
export WEB3_INFURA_PROJECT_ID=$(aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-west-1:342684350154:secret:boost-bot/infura-id-zb9i9o | jq -r ".SecretString" | jq -r ".INFURA_ID")
export GITHUB_TOKEN=$(aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-west-1:342684350154:secret:boost-bot/github-token-QP6NxX | jq -r ".SecretString" | jq -r ".GITHUB_TOKEN")
brownie run scripts/rewards/propose_boost.py --network=mainnet