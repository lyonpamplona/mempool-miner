# Configuração

## Arquivo de ambiente

Copie .env.example para .env. O arquivo real é ignorado pelo Git.

### Credenciais RPC

| Variável | Exemplo seguro | Descrição |
|---|---|---|
| REGTEST_RPC_USER / REGTEST_RPC_PASSWORD | valores exclusivos | credencial do nó Regtest |
| SIGNET_RPC_USER / SIGNET_RPC_PASSWORD | valores exclusivos | credencial do nó Signet |
| MAINNET_RPC_USER / MAINNET_RPC_PASSWORD | valores exclusivos | credencial do profile Mainnet |
| RPC_USER / RPC_PASSWORD | fallback legado | aceito somente para migrar `.env` antigo |

Cada ingestor falha cedo quando a credencial efetiva não está definida. As
variáveis específicas prevalecem sobre o fallback e permitem rotação por nó. O
Compose injeta em cada serviço somente sua credencial; a API HTTP não recebe
nenhuma delas. A passagem por ambiente/argumento ainda é de laboratório:
`rpcauth` e secrets continuam necessários para produção.

### Bitcoin

| Variável | Padrão | Valores/efeito |
|---|---|---|
| DEFAULT_REALM_ID | regtest | realm usado pelos aliases legados |
| SIGNET_PRUNE_MIB | 2048 | alvo de blocos retidos pela Signet |
| MAINNET_PRUNE_MIB | 10240 | alvo Mainnet; mínimo operacional deve ser revisto |
| MAINNET_DBCACHE_MIB | 450 | cache do nó Mainnet sob limite de memória |

`BITCOIN_NETWORK`, `REALM_ID`, hosts e portas são definidos por serviço no
Compose. Não os copie para URLs vindas do usuário. O catálogo público aceita
somente `regtest`, `signet` e `mainnet`.

### Aplicação

| Variável | Padrão | Descrição |
|---|---:|---|
| GAME_MODE | mempool | identificador enviado em game_start |
| BACKEND_IMAGE | mempool-miner-backend:local | tag compartilhada por API/ingestores |
| HIGH_FEE_RATE_SAT_VB | 20 | limiar para a flag is_high_fee |
| TX_QUEUE_MAX_SIZE | 5000 | máximo por ingestor; Mainnet usa 20000 |
| TX_PROCESS_INTERVAL_SECONDS | 1.0 | intervalo por ingestor; Mainnet usa 0.25 |
| LOG_LEVEL | INFO | DEBUG, INFO, WARNING ou ERROR |
| CORS_ORIGINS | localhost:8010 | origens diretas separadas por vírgula |
| ENABLE_API_DOCS | false | habilita Swagger/OpenAPI somente para desenvolvimento direto |
| TRUSTED_HOSTS | derivado de CORS | allowlist opcional de Host, sem `*` |
| REDIS_URL | redis://redis:6379 | injetada pelo Compose |

Valores numéricos inválidos impedem o import do serviço; valide .env antes de
subir.

## Configuração do jogo/PWA

index.html contém:

    <meta name="api-base-url" content="/">

Barra significa mesma origem. Em produção, preserve esse valor e encaminhe
somente `/api/` e `/ws/` pelo proxy do jogo. O service worker não armazena essas
rotas, healthchecks ou rankings.

## Portas

| Porta | Publicada | Uso |
|---:|---|---|
| 8010 | 127.0.0.1 | Nginx do jogo/PWA, proxy REST/WebSocket e documentação em `/docs/` |
| 8000 | somente rede Docker | FastAPI |
| 6379 | somente rede Docker | Redis |
| 28332 | somente rede Docker | ZMQ |
| RPC da rede | somente rede Docker | Bitcoin JSON-RPC |

Para acesso remoto, coloque um proxy TLS confiável à frente e altere o bind da
porta 8010 conscientemente. A documentação em `/docs/` não encaminha a API.
Não publique Redis, RPC ou ZMQ.

## Redes Docker

- edge: frontend e API;
- app_data: API, Redis e ingestores; marcada internal;
- btc_regtest, btc_signet e btc_mainnet: RPC/ZMQ exclusivos por nó;
- signet_p2p e mainnet_p2p: saída dos nós públicos, sem portas no host.

A documentação é servida pelo próprio nginx do jogo (mesma imagem, `/docs/`)
e não exige serviço, perfil ou rede separada.

Signet/Mainnet usam `gw_priority: 1` na rede P2P. Isso requer Docker Compose
2.33.1 ou superior; versões anteriores devem ser atualizadas antes do `up`.
Consulte a referência oficial de
[`gw_priority`](https://docs.docker.com/reference/compose-file/services/#gw_priority).

## Perfis e volumes

| Realm | Inicialização | Volume | Pruning |
|---|---|---|---|
| Regtest | padrão | lógico `bitcoin_data`; físico `mempool-miner_bitcoin_data` preservado | desativado |
| Signet | padrão | `bitcoin_signet_data` | 2048 MiB |
| Mainnet | `--profile mainnet` | `bitcoin_mainnet_data` | 10240 MiB |

O profile `mainnet` não cria volume nem altera qualquer realm; ele publica
somente o nó Mainnet podado e seu ingestor.

Nunca monte o mesmo datadir em duas chains. `docker compose down --volumes`
remove blockchain e ranking e só deve ser usado com intenção explícita.

## Segredos em produção

O Compose ainda fornece cada credencial RPC via `.env`/argumentos, aceitável
apenas para laboratório. `RPC_PASSWORD_FILE` já é suportado pelo ingestor, mas o nó
também precisa migrar para `rpcauth` antes de produção:

1. gere rpcauth com a ferramenta oficial do Bitcoin Core;
2. use um secret manager;
3. elimine senha da linha de comando/inspect;
4. rotacione credenciais por ambiente;
5. restrinja RPC à subnet exata;
6. monitore tentativas de autenticação.

## Compatibilidade Redis

A topologia entregue usa um único Redis 7.4 standalone. Os commits fenced e a
migração legada executam scripts Lua com várias chaves. Redis Cluster não é
suportado nesta versão; migrar exige alinhar todas as hash-tags/slots ou separar
os commits por realm sem perder atomicidade.

## Recursos

Os blocos deploy.resources documentam limites pretendidos. Confirme se a sua
implementação de Compose os aplica:

    docker compose stats
    docker inspect mempool-miner-backend-1

O nome exato do contêiner pode variar.
