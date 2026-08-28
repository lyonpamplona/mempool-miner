# Arquitetura

## Resumo

Mempool Miner é uma aplicação orientada a eventos. Bitcoin Core produz sinais,
o backend os transforma em eventos de domínio, Redis os distribui e o browser
materializa uma partida local.

~~~mermaid
flowchart TB
    subgraph Data["Rede de dados"]
      R["Core Regtest"]
      S["Core Signet"]
      M["Core Mainnet pruned<br>profile opcional"]
      IR["Ingestor Regtest"]
      IS["Ingestor Signet"]
      IM["Ingestor Mainnet"]
      Redis[("Redis 7.4<br>namespace por realm")]
      API["FastAPI<br>sem RPC/ZMQ"]
      R --> IR
      S --> IS
      M -.-> IM
      IR --> Redis
      IS --> Redis
      IM -.-> Redis
      Redis --> API
    end
    subgraph Edge["Rede de borda"]
      GameNginx["Nginx do jogo/PWA<br>:8010 local · /docs/"]
      Browser["Jogador"]
      API <--> GameNginx
      GameNginx <--> Browser
      Reader["Leitor"]
      GameNginx <--> Reader
    end
~~~

## Camadas

### Fonte de eventos

Cada Bitcoin Core publica rawtx e hashblock na porta ZMQ interna 28332 de sua
própria rede Docker. O JSON-RPC complementa cada transação com vsize e taxa
base. RPC e ZMQ não são publicados no host, e cada nó usa volume independente.

Regtest e Signet pertencem ao conjunto padrão. Mainnet só existe quando o
profile `mainnet` é solicitado; usa pruning configurável, `txindex=0` e wallet
desabilitada.

Limite importante: rawtx é uma notificação, não um espelho perfeito da mempool.
Eventos podem repetir e o backlog pode atravessar um bloco. O contador mostrado
deve ser lido como uma aproximação reconciliada, não como consenso.

### Ingestão e domínio

Cada contêiner `ingestor-*` executa exatamente um BitcoinZMQListener, uma fila
limitada e um GameEngine. O terceiro frame ZMQ vira `source_sequence`; a sessão
do socket, origem, realm e epoch acompanham todo evento. Fila cheia descarta
rawtx de forma medida sem impedir a leitura de um bloco.

GameEngine:

1. calcula uma palavra BIP39 determinística a partir do TXID;
2. consulta getmempoolentry;
3. calcula taxa efetiva em satoshis por vbyte;
4. classifica raridade e tamanho.

O ingestor aplica os efeitos de eventos globais ativos (`fee_spike`,
`golden_rush`, `mempool_flood`, `lightning_storm`) antes de publicar a
transação: o `multiplier` do evento já reflete o bônus do evento em curso.

A taxa de consumo é configurável por ingestor. A epoch muda em cada bloco e o
backlog antigo é descartado. Uma barreira serializa TX, reconciliação e bloco;
scripts Redis só confirmam a mutação se a lease ainda pertencer à instância.
Mainnet usa fila/cadência maiores, mas ainda exige batching/sampling para
tráfego de pico.

### Distribuição e persistência

Redis possui três papéis, sempre sob um namespace privado por realm:

- canal `events` para fan-out;
- estado, epoch e contador observado da rede;
- Sorted Set `leaderboard` para os recordes daquele realm.

AOF está habilitado e o volume redis_data mantém dados entre recriações normais.
Pub/Sub não é persistente: clientes desconectados perdem eventos.

### API e tempo real

FastAPI publica catálogo/health/leaderboard por realm e o WebSocket
`/ws/v1/game/{realm_id}`. Ele não conhece credenciais RPC nem abre ZMQ. Cada
cliente recebe `game_start` e somente o canal do realm escolhido. Os aliases
`/api/leaderboard` e `/ws/game` apontam temporariamente para Regtest.

Cada realm mantém um `EventRelay` persistente: uma única assinatura PubSub no
Redis que distribui cada evento para **todas** as filas de clientes WebSocket
conectados (fan-out/broadcast). O relay é criado quando o primeiro cliente
conecta e encerrado quando o último desconecta (contador de conexões por
realm). Antes da correção de 20/08/2026, o `ws_sender` consumia o evento de
uma única fila (round-robin), então com dois ou mais clientes cada um
recebia apenas uma fração dos eventos.

### Apresentação e publicação

O Nginx do jogo publica o shell PWA em `/`, encaminha `/api/` e `/ws/` ao
FastAPI e serve a documentação sanitizada em `/docs/` (mesma imagem, allowlist
de HTML, CSS, JS e SVG). A documentação não encaminha a API. O fallback do jogo
não responde por rotas de documentação.

O browser controla as regras atuais da partida. Essa decisão simplifica a
demonstração, mas impede um ranking confiável.

## Fronteiras de confiança

~~~mermaid
flowchart LR
    Internet((Usuário)) -->|não confiável| GameNginx[Nginx do jogo]
    GameNginx -->|JSON validado| API
    API -->|app_data| Redis
    Redis <-->|app_data| I[Ingestor]
    I -->|RPC/ZMQ em rede exclusiva| BTC[Bitcoin Core]
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
| fila de ingestão | ingestor do realm | buffer 50 000 tx | limitada, sem replay; retry RPC com backoff exponencial |
| contador/epoch/status | Redis por realm | AOF | reconciliação RPC + heartbeat; verificação de epoch no frontend com reconexão automática |
| recordes | Redis Sorted Set por realm | AOF | maior valor por nickname |
| saldo e upgrades | browser | sessionStorage (9 pontos críticos) | manipulável; restaurado ao recarregar página |
| sessão do jogador | browser | sessionStorage via `saveSessionState`/`loadSessionState` | reconexão automática com `realmIdOverride` |
| blockchain | Bitcoin Core | volume | garantia do nó |

### Persistência de sessão (frontend)

O estado da partida é salvo em `sessionStorage` em 9 pontos críticos:
saldo, nível de hardware, status Lightning, progresso RBF, resultado final,
entre outros. Ao recarregar a página (F5), `loadSessionState()` restaura o
estado e `startSession()` aceita `realmIdOverride` para reconectar ao mesmo
realm automaticamente. `clearSessionState()` limpa tudo ao encerrar a partida.

### Estabilidade do ingestor

O ingestor aplica retry com backoff exponencial em chamadas RPC falhas e
mantém um buffer de até 50 000 transações para absorver picos de mempool
sem descartar eventos prematuramente.

## Disponibilidade

Healthchecks distinguem disponibilidade RPC de IBD. A API depende apenas do
Redis: Signet sincronizando ou Mainnet desligada não derrubam o catálogo. Cada
ingestor mantém lease renovável; commits com token antigo são recusados e o
healthcheck valida a identidade local. Cada realm ainda tem um único nó e não há
HA entre duas origens da mesma chain.

## Decisões registradas

### ADR-001 — Ingestão separada da API

Cada origem roda em `python -m app.ingestor`; Uvicorn atende apenas Redis/HTTP.
Isso elimina a multiplicação de eventos ao escalar futuramente a API.

### ADR-005 — Realm, network e node são identidades diferentes

`network` descreve a chain, `realm_id` isola jogo/ranking e `node_id` identifica
a origem física internamente. O cliente recebe e escolhe somente realms
sanitizados do catálogo e nunca fornece endpoints RPC/ZMQ.

### ADR-006 — Mainnet é opt-in e podada

Nó e ingestor Mainnet compartilham `profiles: [mainnet]`. O `up` padrão não os
cria. Pruning reduz retenção de blocos, não o custo de download/validação do IBD.

### ADR-002 — Proxy same-origin

Frontend não conhece portas internas. Nginx centraliza HTTP/WebSocket e prepara
o caminho para TLS.

### ADR-007 — Jogo e documentação na mesma origem, superfícies separadas

O PWA da porta 8010 não contém protótipos, Markdown, Swagger ou OpenAPI. A
documentação é servida em `/docs/` pelo mesmo nginx, com allowlist estática de
HTML, CSS, JS e SVG sanitizados. A separação por prefixo evita que o fallback
do jogo masque links quebrados ou exponha artefatos internos.

### ADR-003 — Sem sobreposição de palavras

Palavras não compartilham células. Isso evita que uma célula marcada como
encontrada bloqueie outra palavra cruzada.

### ADR-004 — Documentar simulação

Termos de Bitcoin permanecem na narrativa, mas toda interface pública informa
que saldo, mineração e Lightning são simulados.

## Arquitetura-alvo

O próximo desenho recomendado acrescenta:

- serviço de partidas autoritativo;
- HA com múltiplos nós por realm, eleição e deduplicação por TXID/hash;
- gateway/API horizontalmente escalável;
- fila durável ou stream para replay;
- identidade de jogador e eventos de pontuação assinados;
- métricas, tracing e alertas.

Essa migração está detalhada em [ROADMAP.md](ROADMAP.md).
