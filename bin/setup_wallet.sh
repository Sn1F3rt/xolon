#!/bin/bash

set -e
set +x

# these are only used for local development
WALLET_PATH="$HOME/data/xolon/wallet"
WALLET_PASS="knz7FlihIGfhdDZHKkC3W+xgYTp1G+jE9U1BaXduw"
WALLET_RPC_USER="xolon"
WALLET_RPC_PASS="123sfj12joiasd1293aAWE!#"
DAEMON_URI="https://node.suchwow.xyz:443"

# create new wallet path
mkdir -p $WALLET_PATH

if [ ! -d "$WALLET_PATH" ]; then
  # initialize new wallet and retain seed
  docker run --rm -it --name xolon-wallet-init \
    -v $WALLET_PATH:/root \
    lalanza808/xolentum \
    xolentum-wallet-cli \
      --daemon-address $DAEMON_URI \
      --generate-new-wallet /root/wow \
      --password $WALLET_PASS
fi

# setup rpc process
docker run --rm -d --name xolon-wallet \
  -v $WALLET_PATH:/root \
  -p 9999:9999 \
  lalanza808/xolentum \
  xolentum-wallet-rpc \
    --daemon-address $DAEMON_URI \
    --wallet-file /root/wow \
    --password $WALLET_PASS \
    --rpc-bind-port 9999 \
    --rpc-bind-ip 0.0.0.0 \
    --confirm-external-bind \
    --rpc-login "$WALLET_RPC_USER:$WALLET_RPC_PASS" \
    --log-file /root/rpc.log
