# Arquitetura

## Resumo

Mempool Miner é uma aplicação orientada a eventos. Bitcoin Core produz sinais,
o backend os transforma em eventos de domínio, Redis os distribui e o browser
materializa uma partida local.

~~~mermaid
flowchart TB
    subgraph Data["Rede de dados"]
      BTC["Bitcoin Core 31.1<br>RPC + ZMQ"]
      Redis[("Redis 7.4<br>Pub/Sub + Sorted Set")]
      API["FastAPI<br>1 worker"]
      Queue[["asyncio.Queue<br>máx. 5.000"]]
      Engine["GameEngine<br>BIP39 + RPC"]
      BTC -->|rawtx/hashblock| Queue
      Queue --> Engine
      Engine -->|getmempoolentry| BTC
      Engine --> Redis
      Redis --> API
    end
    subgraph Edge["Rede de borda"]
      Nginx["Nginx<br>:8010 local"]
      Browser["Navegador"]
      API <--> Nginx
      Nginx <--> Browser
    end
~~~

## Camadas

### Fonte de eventos

Bitcoin Core publica rawtx e hashblock na porta ZMQ interna 28332. O JSON-RPC
complementa cada transação com vsize e taxa base. O nó não é exposto no host.

Limite importante: rawtx é uma notificação, não um espelho perfeito da mempool.
Eventos podem repetir e o backlog pode atravessar um bloco. O contador mostrado
deve ser lido como uma aproximação reconciliada, não como consenso.

### Ingestão e domínio

BitcoinZMQListener converte bytes em hexadecimal e aplica backpressure por meio
de uma fila limitada. Um único processo consome essa fila; executar vários
workers duplicaria todos os eventos PUB/SUB.

GameEngine:

1. calcula uma palavra BIP39 determinística a partir do TXID;
2. consulta getmempoolentry;
3. calcula taxa efetiva em satoshis por vbyte;
4. classifica raridade e tamanho.

A taxa de consumo é configurável. O padrão de um item por segundo protege a UI,
mas não acompanha necessariamente todo o tráfego de mainnet.

### Distribuição e persistência

Redis possui três papéis:

- canal game_events para fan-out;
- chave mempool_count para o contador reconciliado/observado;
- Sorted Set global_leaderboard para o recorde de cada nickname.

AOF está habilitado e o volume redis_data mantém dados entre recriações normais.
Pub/Sub não é persistente: clientes desconectados perdem eventos.

### API e tempo real

FastAPI publica REST para healthcheck/leaderboard e um WebSocket de jogo. Cada
cliente recebe primeiro game_start e depois os eventos do canal Redis. O
OpenAPI gerado cobre REST; eventos WebSocket estão documentados manualmente.

### Apresentação

Nginx é a única porta publicada. Ele serve o jogo, a apresentação e a
documentação, encaminha /api ao FastAPI e faz upgrade de /ws. Isso evita portas
fixas no JavaScript e mixed content quando TLS for colocado na borda.

O browser controla as regras atuais da partida. Essa decisão simplifica a
demonstração, mas impede um ranking confiável.

## Fronteiras de confiança

~~~mermaid
flowchart LR
    Internet((Usuário)) -->|não confiável| Nginx
    Nginx -->|JSON validado| API
    API -->|rede privada| Redis
    API -->|credencial RPC| BTC[Bitcoin Core]
    BTC -->|bytes não confiáveis| Listener
~~~

- nickname e score são entrada hostil;
- mensagens do Redis/ZMQ precisam de esquema e limites;
- .env e cookie/credencial RPC nunca devem entrar no Git;
- HTML não pode ser montado com strings recebidas;
- saldo e score do browser não são autoridade.

## Estado e consistência

| Estado | Dono atual | Persistência | Garantia |
|---|---|---|---|
| transações pendentes da rodada | browser | nenhuma | melhor esforço |
| fila de ingestão | processo FastAPI | nenhuma | limitada, sem replay |
| contador observado | Redis | AOF | aproximação |
| recordes | Redis Sorted Set | AOF | maior valor por nickname |
| saldo e upgrades | browser | nenhuma | manipulável |
| blockchain | Bitcoin Core | volume | garantia do nó |

## Disponibilidade

Healthchecks formam a cadeia Bitcoin/Redis → backend → frontend. O Compose
reinicia serviços, mas não há alta disponibilidade: o ingeridor é singleton e
Redis/Bitcoin são instâncias únicas.

## Decisões registradas

### ADR-001 — Um worker no backend

Aceita-se menor escala da API para impedir múltiplos subscribers ZMQ. A evolução
correta é separar ingestão e API, não aumentar workers do processo atual.

### ADR-002 — Proxy same-origin

Frontend não conhece portas internas. Nginx centraliza HTTP/WebSocket e prepara
o caminho para TLS.

### ADR-003 — Sem sobreposição de palavras

Palavras não compartilham células. Isso evita que uma célula marcada como
encontrada bloqueie outra palavra cruzada.

### ADR-004 — Documentar simulação

Termos de Bitcoin permanecem na narrativa, mas toda interface pública informa
que saldo, mineração e Lightning são simulados.

## Arquitetura-alvo

O desenho recomendado separa:

- ingestor singleton com sequência ZMQ, deduplicação e reconciliação;
- serviço de partidas autoritativo;
- gateway/API horizontalmente escalável;
- fila durável ou stream para replay;
- identidade de jogador e eventos de pontuação assinados;
- métricas, tracing e alertas.

Essa migração está detalhada em [ROADMAP.md](ROADMAP.md).
