#!/bin/bash
# Script de entrada para Bitcoin Core regtest
# Cria wallet, gera blocos e envia transações para o mempool
#
# IMPORTANTE: este script NUNCA deve encerrar o container. Se o RPC demorar
# a ficar pronto (cold start), ele continua aguardando em loop — o bitcoind
# é o processo principal (wait $BITCOIND_PID) e o container só sai quando o
# bitcoind sai.

RPC_USER="${REGTEST_RPC_USER:-mempool_regtest}"
RPC_PASSWORD="${REGTEST_RPC_PASSWORD:-Nakamoto1}"
RPC_PORT=18443

# Função: executa bitcoin-cli com credenciais
# Usa o PATH (bitcoin-cli está em /opt/bitcoin-31.1/bin no container)
rpc() {
    bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcport="$RPC_PORT" "$@"
}

# Função: aguarda RPC ficar disponível (até 300s, sem crashar)
wait_for_rpc() {
    echo "[entrypoint] Aguardando RPC regtest..."
    for i in $(seq 1 150); do
        if rpc getblockcount >/dev/null 2>&1; then
            echo "[entrypoint] RPC regtest disponível (tentativa $i)"
            return 0
        fi
        sleep 2
    done
    echo "[entrypoint] RPC ainda não disponível após 300s — continuando a aguardar em background"
    return 1
}

echo "[entrypoint] Iniciando Bitcoin Core regtest..."

# Inicia o bitcoind em background
bitcoind -conf=/etc/bitcoin/bitcoin.conf -datadir=/home/bitcoin/.bitcoin -chain=regtest "$@" &
BITCOIND_PID=$!
echo "[entrypoint] bitcoind iniciado (PID $BITCOIND_PID)"

# Aguarda RPC ficar disponível (sem crashar se demorar)
if wait_for_rpc; then
    # Cria wallet se não existir
    if ! rpc listwallets 2>/dev/null | grep -q '"miner"'; then
        rpc createwallet miner 2>/dev/null
        echo "[entrypoint] Wallet 'miner' criada"
    else
        echo "[entrypoint] Wallet 'miner' já existe"
    fi

    # Carrega a wallet (Bitcoin Core 31 não carrega automaticamente)
    rpc loadwallet miner 2>/dev/null || true

    # Verifica se precisa gerar blocos (mínimo 150)
    BLOCKS=$(rpc -rpcwallet=miner getblockcount 2>/dev/null)
    if [ -n "$BLOCKS" ] && [ "$BLOCKS" -lt 150 ] 2>/dev/null; then
        echo "[entrypoint] Gerando blocos (atual: $BLOCKS)..."
        rpc -rpcwallet=miner generatetoaddress $((150 - BLOCKS)) "$(rpc -rpcwallet=miner getnewaddress 2>/dev/null)" >/dev/null 2>&1
        echo "[entrypoint] Blocos gerados"
    else
        echo "[entrypoint] Blocos suficientes (atual: $BLOCKS)"
    fi

    # Envia transações para o mempool
    ADDR=$(rpc -rpcwallet=miner getnewaddress 2>/dev/null)
    if [ -n "$ADDR" ]; then
        echo "[entrypoint] Enviando transações para o mempool..."
        for i in $(seq 1 10); do
            rpc -rpcwallet=miner sendtoaddress "$ADDR" 0.001 "" "" false >/dev/null 2>&1
        done
        echo "[entrypoint] 10 transações enviadas"
    fi
else
    # RPC não ficou pronto a tempo — tenta em background sem bloquear o container
    echo "[entrypoint] Tenta configurar wallet/blocos em background..."
    (
        # Aguarda mais 5 min em background
        for i in $(seq 1 150); do
            if rpc getblockcount >/dev/null 2>&1; then
                rpc listwallets 2>/dev/null | grep -q '"miner"' || rpc createwallet miner 2>/dev/null
                rpc loadwallet miner 2>/dev/null || true
                BLOCKS=$(rpc -rpcwallet=miner getblockcount 2>/dev/null)
                if [ -n "$BLOCKS" ] && [ "$BLOCKS" -lt 150 ] 2>/dev/null; then
                    rpc -rpcwallet=miner generatetoaddress $((150 - BLOCKS)) "$(rpc -rpcwallet=miner getnewaddress 2>/dev/null)" >/dev/null 2>&1
                fi
                ADDR=$(rpc -rpcwallet=miner getnewaddress 2>/dev/null)
                if [ -n "$ADDR" ]; then
                    for i in $(seq 1 10); do
                        rpc -rpcwallet=miner sendtoaddress "$ADDR" 0.001 "" "" false >/dev/null 2>&1
                    done
                fi
                echo "[entrypoint] Configuração concluída em background"
                break
            fi
            sleep 2
        done
    ) &
fi

# Mantém o container vivo aguardando o bitcoind (child process)
echo "[entrypoint] Aguardando bitcoind..."
wait "$BITCOIND_PID"
