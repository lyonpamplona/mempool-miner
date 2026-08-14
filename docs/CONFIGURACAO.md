# Configuração

## Arquivo de ambiente

Copie .env.example para .env. O arquivo real é ignorado pelo Git.

### Obrigatórias

| Variável | Exemplo seguro | Descrição |
|---|---|---|
| RPC_USER | mempool_app | usuário exclusivo do backend |
| RPC_PASSWORD | valor aleatório | senha longa; nunca use a amostra |

O backend falha cedo quando uma dessas variáveis não está definida. Isso evita
credenciais silenciosas embutidas no código.

### Bitcoin

| Variável | Padrão | Valores/efeito |
|---|---|---|
| BITCOIN_NETWORK | regtest | regtest, signet ou main |
| RPC_HOST | bitcoind | hostname RPC visto pelo backend |
| RPC_PORT | 18443 | 18443 regtest, 38332 signet, 8332 main |
| ZMQ_HOST | bitcoind | hostname do publisher ZMQ |
| ZMQ_PORT | 28332 | porta configurada em bitcoin.conf |

BITCOIN_NETWORK e RPC_PORT devem sempre formar um par coerente.

### Aplicação

| Variável | Padrão | Descrição |
|---|---:|---|
| GAME_MODE | mempool | identificador enviado em game_start |
| HIGH_FEE_RATE_SAT_VB | 20 | limiar para a flag is_high_fee |
| TX_QUEUE_MAX_SIZE | 5000 | máximo de transações aguardando |
| TX_PROCESS_INTERVAL_SECONDS | 1.0 | intervalo entre publicações |
| LOG_LEVEL | INFO | DEBUG, INFO, WARNING ou ERROR |
| CORS_ORIGINS | localhost:8010 | origens diretas separadas por vírgula |
| REDIS_URL | redis://redis:6379 | injetada pelo Compose |

Valores numéricos inválidos impedem o import do serviço; valide .env antes de
subir.

## Configuração do frontend

index.html contém:

    <meta name="api-base-url" content="/">

Barra significa mesma origem. Para servir o HTML sem Nginx durante
desenvolvimento, informe uma URL absoluta que exponha REST e WebSocket.

## Portas

| Porta | Publicada | Uso |
|---:|---|---|
| 8010 | 127.0.0.1 | Nginx, jogo e documentação |
| 8000 | somente rede Docker | FastAPI |
| 6379 | somente rede Docker | Redis |
| 28332 | somente rede Docker | ZMQ |
| RPC da rede | somente rede Docker | Bitcoin JSON-RPC |

Para acesso remoto, coloque um proxy TLS confiável à frente e altere o bind da
porta 8010 conscientemente. Não publique Redis, RPC ou ZMQ.

## Redes Docker

- edge: frontend e backend;
- data: backend, Redis e Bitcoin; marcada internal;
- p2p: somente Bitcoin, para saída à rede quando signet/main forem usados.

## Segredos em produção

O Compose atual usa .env e argumentos de processo, aceitáveis apenas para
laboratório. Em produção:

1. gere rpcauth com a ferramenta oficial do Bitcoin Core;
2. use um secret manager;
3. elimine senha da linha de comando/inspect;
4. rotacione credenciais por ambiente;
5. restrinja RPC à subnet exata;
6. monitore tentativas de autenticação.

## Recursos

Os blocos deploy.resources documentam limites pretendidos. Confirme se a sua
implementação de Compose os aplica:

    docker compose stats
    docker inspect mempool-miner-backend-1

O nome exato do contêiner pode variar.
