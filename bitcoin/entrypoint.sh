#!/bin/bash
# Script de entrada para Bitcoin Core com credenciais dinâmicas

# Gera o arquivo de configuração com as credenciais corretas
cat > /etc/bitcoin/bitcoin.conf << EOF
# Configuração comum. Prune, dbcache e mempool são definidos por serviço.
txindex=0
maxconnections=40

server=1
rpcallowip=0.0.0.0/0

zmqpubhashblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28332
zmqpubsequence=tcp://0.0.0.0:28332

[regtest]
rpcport=18443
rpcuser=${REGTEST_RPC_USER:-mempool_regtest}
rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1}

[signet]
rpcport=38332
rpcuser=${SIGNET_RPC_USER:-mempool_signet}
rpcpassword=${SIGNET_RPC_PASSWORD:-Nakamoto2}

[main]
rpcport=8332
rpcuser=${MAINNET_RPC_USER:-mempool_mainnet}
rpcpassword=${MAINNET_RPC_PASSWORD:-Nakamoto3}
EOF

# Executa o bitcoind com a configuração gerada
exec /entrypoint.sh -conf=/etc/bitcoin/bitcoin.conf -datadir=/home/bitcoin/.bitcoin -chain=$BITCOIN_NETWORK "$@"
