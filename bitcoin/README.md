<p align="center"><img src="../docs/assets/bitcoin.svg" width="96" alt="Ícone animado do Bitcoin Core"></p>

# Bitcoin Core

O nó fornece a fonte de eventos do jogo. O arquivo bitcoin.conf contém apenas
parâmetros não secretos; usuário e senha RPC vêm do arquivo .env no momento em
que o Compose inicia o contêiner.

## Tópicos configurados

| Tópico | Corpo | Uso |
|---|---|---|
| rawtx | transação serializada | gerar TXID e palavra |
| hashblock | hash de bloco | encerrar/reiniciar a rodada |
| sequence | evento de mempool | publicado; consumo semântico completo é roadmap |

O listener atual assina `rawtx` e `hashblock` e lê o contador do terceiro frame
ZMQ. O tópico `sequence` foi habilitado para a próxima fase de reconciliação.

## Redes

| Rede | RPC | P2P | Uso recomendado |
|---|---:|---:|---|
| regtest | 18443 | 18444 | desenvolvimento local |
| signet | 38332 | 38333 | integração pública controlada |
| mainnet | 8332 | 8333 | profile opcional, podado e com wallet desabilitada |

Regtest e Signet sobem por padrão; Mainnet exige `--profile mainnet`. Cada nó
tem volume, rede interna e ingestor próprios. RPC e ZMQ não são publicados no
host. Exemplos:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'
    docker compose exec bitcoin-signet sh -lc 'bitcoin-cli -signet -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'
    docker compose --profile mainnet exec bitcoin-mainnet sh -lc 'bitcoin-cli -chain=main -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'

Mainnet usa `MAINNET_PRUNE_MIB=10240` por padrão. Pruning reduz retenção, mas o
IBD ainda baixa e valida toda a cadeia e requer espaço adicional para chainstate.

## Aviso de imagem

A imagem bitcoin/bitcoin usada pelo Compose é adequada ao laboratório, mas seu
próprio mantenedor declara que ela não é uma imagem oficial do projeto Bitcoin
Core. Para produção, verifique binários e assinaturas ou mantenha uma imagem
interna reproduzível.
