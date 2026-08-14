<p align="center"><img src="../docs/assets/bitcoin.svg" width="96" alt="Ícone animado do Bitcoin Core"></p>

# Bitcoin Core

O nó fornece a fonte de eventos do jogo. O arquivo bitcoin.conf contém apenas
parâmetros não secretos; usuário e senha RPC vêm do arquivo .env no momento em
que o Compose inicia o contêiner.

## Tópicos consumidos

| Tópico | Corpo | Uso |
|---|---|---|
| rawtx | transação serializada | gerar TXID e palavra |
| hashblock | hash de bloco | encerrar/reiniciar a rodada |

## Redes

| Rede | RPC | P2P | Uso recomendado |
|---|---:|---:|---|
| regtest | 18443 | 18444 | desenvolvimento local |
| signet | 38332 | 38333 | integração pública controlada |
| main | 8332 | 8333 | somente após hardening e revisão operacional |

Ao trocar BITCOIN_NETWORK, ajuste também RPC_PORT no .env. RPC e ZMQ não são
publicados no host; use docker compose exec bitcoind bitcoin-cli para operar o
nó.

## Aviso de imagem

A imagem bitcoin/bitcoin usada pelo Compose é adequada ao laboratório, mas seu
próprio mantenedor declara que ela não é uma imagem oficial do projeto Bitcoin
Core. Para produção, verifique binários e assinaturas ou mantenha uma imagem
interna reproduzível.
