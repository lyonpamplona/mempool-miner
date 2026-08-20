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

# Para regtest: cria e carrega wallet automaticamente
if [ "$BITCOIN_NETWORK" = "regtest" ]; then
    echo "[entrypoint] Iniciando Bitcoin Core regtest..."

    # Inicia o bitcoind em background para preparar a wallet
    /entrypoint.sh -conf=/etc/bitcoin/bitcoin.conf -datadir=/home/bitcoin/.bitcoin -chain=regtest -daemon "$@"

    # Aguarda RPC ficar disponivel
    echo "[entrypoint] Aguardando RPC regtest..."
    for i in $(seq 1 60); do
        if /usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 getblockcount >/dev/null 2>&1; then
            echo "[entrypoint] RPC regtest disponivel"
            break
        fi
        sleep 2
    done

    # Cria wallet se nao existir
    if ! /usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 loadwallet miner 2>/dev/null | grep -q '"name"'; then
        /usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 createwallet miner 2>/dev/null
        echo "[entrypoint] Wallet 'miner' criada"
    else
        echo "[entrypoint] Wallet 'miner' carregada"
    fi

    # Verifica se precisa gerar blocos (menos de 150)
    BLOCKS=$(/usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 -rpcwallet=miner getblockcount 2>/dev/null)
    if [ "$BLOCKS" -lt 150 ] 2>/dev/null; then
        echo "[entrypoint] Gerando blocos (atual: $BLOCKS)..."
        /usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 -rpcwallet=miner -generate $((150 - BLOCKS)) >/dev/null 2>&1
        echo "[entrypoint] Blocos gerados"
    fi

    # Envia transacoes para o mempool
    ADDR=$(/usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 -rpcwallet=miner getnewaddress 2>/dev/null)
    if [ -n "$ADDR" ]; then
        echo "[entrypoint] Enviando transacoes para o mempool..."
        for i in $(seq 1 10); do
            /usr/bin/bitcoin-cli -regtest -rpcuser=${REGTEST_RPC_USER:-mempool_regtest} -rpcpassword=${REGTEST_RPC_PASSWORD:-Nakamoto1} -rpcport=18443 -rpcwallet=miner sendtoaddress "$ADDR" 0.001 "" "" false >/dev/null 2>&1
        done
        echo "[entrypoint] 10 transacoes enviadas"
    fi

    # Mantem o bitcoind rodando (ja esta em daemon)
    wait
else
    # Executa o bitcoind normalmente para signet/mainnet
    exec /entrypoint.sh -conf=/etc/bitcoin/bitcoin.conf -datadir=/home/bitcoin/.bitcoin -chain=$BITCOIN_NETWORK "$@"
fi
