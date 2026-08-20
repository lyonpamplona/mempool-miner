# Relatório de arquitetura multi-rede

## Resultado

O projeto suporta três nós Bitcoin Core independentes na mesma topologia
Docker. Regtest e Signet pertencem ao conjunto padrão. Mainnet permanece
desativada por padrão, exige o profile `mainnet` e opera com pruning.

Neste documento, **multi-node** significa um nó por chain/realm. Alta
disponibilidade com dois nós da mesma chain ainda não está implementada.

| Realm | Serviço Core | Ingestor | Inicialização | Datadir | Política |
|---|---|---|---|---|---|
| regtest | `bitcoin-regtest` | `ingestor-regtest` | padrão | `bitcoin_data` | sem pruning, wallet de laboratório |
| signet | `bitcoin-signet` | `ingestor-signet` | padrão | `bitcoin_signet_data` | prune 2048 MiB, wallet desabilitada |
| mainnet | `bitcoin-mainnet` | `ingestor-mainnet` | profile `mainnet` | `bitcoin_mainnet_data` | prune 10240 MiB, txindex 0, wallet desabilitada |

## Como iniciar

Sem Mainnet:

    docker compose config --quiet
    docker compose up -d --build

Incluindo Mainnet explicitamente:

    docker compose --profile mainnet config --quiet
    docker compose --profile mainnet up -d --build

Para desligar somente a Mainnet:

    docker compose --profile mainnet stop ingestor-mainnet bitcoin-mainnet

O profile ausente não torna a API unhealthy. O catálogo continua retornando o
realm Mainnet com `playable=false`/`status=disabled` até ele ser iniciado.

## Isolamento aplicado

- cada Core possui volume próprio; um datadir nunca é compartilhado por chains;
- cada par Core/ingestor possui rede de controle interna própria;
- RPC/ZMQ/Redis/FastAPI não publicam portas no host;
- Signet e Mainnet possuem rede P2P externa com gateway explícito;
- cada ingestor valida a chain RPC declarada antes de publicar;
- canal, contador, epoch, estado e leaderboard usam namespace por `realm_id`;
- todos os eventos carregam `network`, `chain`, `realm_id`, `node_id` e epoch;
- a API não abre sockets ZMQ e não recebe credenciais RPC;
- uma lease Redis e commits condicionais ao token impedem duas instâncias de
  gravar simultaneamente no mesmo realm;
- o browser invalida socket, requests e timers ao trocar de realm.

O Redis desta topologia é standalone. Redis Cluster não deve ser ativado sem
redesenhar os scripts Lua multi-chave e os slots do heartbeat/migração.

## Mainnet podada

`MAINNET_PRUNE_MIB=10240` limita a retenção aproximada de blocos/undo, não o
consumo total do datadir. Chainstate e índices ocupam espaço adicional. O IBD
ainda baixa e valida toda a cadeia antes de descartar blocos antigos e pode
consumir banda, CPU e tempo significativos. Consulte a documentação de
[block pruning do Bitcoin Core](https://bitcoincore.org/en/releases/0.11.0/).

Mainnet só deve ser habilitada após:

1. rotacionar as três credenciais RPC de exemplo;
2. dimensionar disco, RAM e banda;
3. validar `docker compose --profile mainnet config`;
4. confirmar que RPC/ZMQ não aparecem em `ports`;
5. substituir senha em argv por `rpcauth`/secrets;
6. validar a imagem/binário Bitcoin por uma cadeia de fornecimento confiável;
7. testar backup, restauração e rollback do volume.

## Migração do estado existente

O volume lógico Regtest continua chamado `bitcoin_data`, preservando o volume
físico `mempool-miner_bitcoin_data` do Compose anterior. Signet e Mainnet sempre
recebem volumes novos. Antes da primeira subida:

1. pare a topologia antiga;
2. confirme que o volume legado contém Regtest;
3. faça backup consistente;
4. execute `docker compose config --quiet`;
5. suba primeiro sem o profile Mainnet;
6. confirme o catálogo e uma partida Regtest;
7. preserve o backup até aprovar o rollback.

Nunca inicie duas versões do Core apontando para o mesmo volume. Não use
`docker compose down --volumes` durante a migração.

## Validação e critérios de aceite

O workflow de CI prepara uma chain Regtest efêmera, inicia o ingestor, envia uma
transação, observa o contador Redis e minera um bloco para verificar a mudança
de epoch. Localmente, valide também:

- Regtest e Signet aparecem separadamente em `/api/v1/networks`;
- `block_mined` de um realm não altera a rodada do outro;
- leaderboards Regtest/Signet não compartilham membros;
- Mainnet não cria contêiner/volume no `up` padrão;
- Mainnet pruned aparece como `playable=true` somente depois do IBD;
- perder a lease encerra o ingestor antigo;
- nenhum host/porta/credencial RPC chega ao navegador.

Docker não estava disponível no host usado para esta implementação. Portanto,
lint, testes unitários, JavaScript, YAML e documentação foram validados
localmente, mas o primeiro build/up real continua sendo critério de aceite.

## Roadmap restante

| Fase | Estado | Próxima entrega |
|---|---|---|
| contratos/namespace por realm | concluída | preservar compatibilidade dos aliases |
| ingestor separado e lease | concluída | métricas e teste de takeover com Redis real |
| Compose Regtest/Signet/Mainnet | concluída estaticamente | executar smoke Docker/CI |
| segredos | parcial | `rpcauth`, secret files e subnet RPC exata |
| sequência/replay | parcial | interpretar tópico `sequence`, gaps e Redis Streams |
| Mainnet operacional | pendente | capacity test, IBD, backup e binário verificado |
| HA por realm | futuro | registry, eleição, dedupe entre nós, reorg e failover |

Detalhes complementares: [Arquitetura](ARQUITETURA.md),
[Configuração](CONFIGURACAO.md), [Deployment](DEPLOYMENT.md),
[Auditoria](AUDITORIA.md) e [Roadmap](ROADMAP.md).
