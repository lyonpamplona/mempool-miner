# Troubleshooting

## A página não abre

    docker compose ps
    docker compose logs --tail 100 frontend backend

Confirme que a porta 8010 não está ocupada. O bind é somente 127.0.0.1.

## Backend unhealthy

    docker compose logs --tail 200 backend
    docker compose exec redis redis-cli ping
    docker compose exec bitcoind bitcoin-cli -regtest getblockchaininfo

Causas frequentes:

- RPC_USER/RPC_PASSWORD ausentes;
- RPC_PORT incompatível com BITCOIN_NETWORK;
- Redis/Bitcoin ainda iniciando;
- senha do backend diferente da passada ao Bitcoin;
- valor numérico inválido no .env.

## “Aguardando transações” não termina

Em regtest nada acontece sozinho. Siga [TUTORIAL.md](TUTORIAL.md) para criar
carteira, minerar 101 blocos e enviar transações.

Outras causas:

- menos de seis palavras únicas;
- listener ZMQ não conectado;
- fila atrasada pelo intervalo de processamento;
- transação já confirmada;
- RPC não encontrou getmempoolentry e houve logs de warning.

Diagnóstico:

    docker compose logs -f backend bitcoind
    docker compose exec bitcoind bitcoin-cli -regtest getrawmempool
    docker compose exec redis redis-cli GET mempool_count

## WebSocket desconecta

No DevTools, confirme /ws/game com status 101. Revise Nginx:

    docker compose logs --tail 100 frontend

Se houver proxy/TLS externo, ele também precisa encaminhar Upgrade e Connection
e permitir timeout longo.

## Ranking vazio ou não atualiza

    Invoke-RestMethod http://localhost:8010/api/leaderboard
    docker compose exec redis redis-cli ZCARD global_leaderboard

HTTP 422 no POST indica nickname/score inválido. Nomes aceitam apenas letras,
números, hífen e sublinhado e têm até 12 caracteres.

## Grade cortada

Recarregue após redimensionar e confirme que style.css/game.js não estão em
cache. O código calcula célula por viewport. Em telas muito estreitas o layout
se torna vertical e a página permite rolagem.

## createwallet informa que já existe

    docker compose exec bitcoind bitcoin-cli -regtest loadwallet miner

Se já estiver carregada, continue usando -rpcwallet=miner.

## Docker não é reconhecido

Instale/inicie Docker Desktop e abra um novo terminal. Este repositório não
inclui o daemon Docker. Em Windows:

    docker context ls
    docker info

## Erro de imagem Bitcoin

Confirme arquitetura, conectividade com Docker Hub e existência da tag:

    docker pull bitcoin/bitcoin:31.1

A imagem é voltada a laboratório. Não troque a tag em um nó persistente sem
backup e teste de compatibilidade.

## Recuperação

Prefira:

    docker compose restart SERVICO
    docker compose up -d --build SERVICO

Não use down --volumes como tentativa genérica: ele remove ranking, carteira e
blockchain local.
