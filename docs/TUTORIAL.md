# Tutorial de uso

## 1. Preparar

Instale Docker Desktop no Windows ou Docker Engine + Compose v2 no Linux.
Confirme:

    docker --version
    docker compose version

Copie a configuração:

PowerShell:

    Copy-Item .env.example .env

Bash:

    cp .env.example .env

Edite .env e troque RPC_PASSWORD. Para o primeiro teste, mantenha:

    BITCOIN_NETWORK=regtest
    RPC_PORT=18443

## 2. Validar e iniciar

    docker compose config --quiet
    docker compose up -d --build
    docker compose ps

Espere todos os serviços ficarem healthy. Acompanhe:

    docker compose logs -f bitcoind redis backend frontend

## 3. Abrir o jogo

Acesse http://localhost:8010, informe um nickname de até 12 caracteres e
conecte. Em regtest a mempool começa vazia, portanto gere atividade.

## 4. Criar transações em regtest

Crie uma carteira de laboratório:

    docker compose exec bitcoind bitcoin-cli -regtest createwallet miner

Obtenha um endereço:

    docker compose exec bitcoind bitcoin-cli -regtest -rpcwallet=miner getnewaddress

Copie o endereço retornado e amadureça saldo de teste:

    docker compose exec bitcoind bitcoin-cli -regtest generatetoaddress 101 ENDERECO

Gere pelo menos seis transações. Para cada uma, crie outro endereço e envie uma
quantidade fictícia:

    docker compose exec bitcoind bitcoin-cli -regtest -rpcwallet=miner getnewaddress
    docker compose exec bitcoind bitcoin-cli -regtest -rpcwallet=miner sendtoaddress ENDERECO 0.001

Repita até o browser receber seis palavras únicas. Colisões são possíveis porque
cada TXID usa apenas a primeira palavra de uma frase BIP39.

Se createwallet informar que a carteira já existe:

    docker compose exec bitcoind bitcoin-cli -regtest loadwallet miner

## 5. Jogar

1. Aguarde a grade aparecer.
2. Arraste horizontal, vertical ou diagonalmente sobre uma palavra.
3. A direção fica fixa após a segunda célula.
4. Encontre todas antes do cronômetro.
5. Use sats fictícios para dica/hardware.
6. Ative Lightning somente entre rodadas.

Para simular um bloco real vencendo a rodada, gere um bloco enquanto joga:

    docker compose exec bitcoind bitcoin-cli -regtest generatetoaddress 1 ENDERECO

## 6. Inspecionar

- ranking: http://localhost:8010/api/leaderboard
- healthcheck: http://localhost:8010/api/health
- Swagger: http://localhost:8010/backend-docs
- API visual: http://localhost:8010/docs/api.html

## 7. Encerrar

Preservando volumes:

    docker compose down

Remover volumes apaga blockchain regtest, carteira e ranking. Use somente se
essa perda for intencional:

    docker compose down --volumes

## O que é real e o que é simulado

| Recurso | Natureza |
|---|---|
| evento ZMQ, TXID, vsize, taxa e hash de bloco | integração real com o nó |
| palavra BIP39 | derivação determinística para o jogo |
| saldo em sats, carteira fria, hashrate e reward | simulação local |
| hardware e dica | mecânica local |
| Lightning/zero-conf | simulação visual |
| leaderboard | Redis real, score não autoritativo |
