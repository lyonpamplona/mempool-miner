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
      GameNginx["Nginx do jogo/PWA<br>:8010 local"]
      Browser["Jogador"]
      API <--> GameNginx
      GameNginx <--> Browser
      DocsNginx["Portal sanitizado<br>:8020 · profile docs"]
      Reader["Leitor"]
      DocsNginx <--> Reader
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

### Apresentação e publicação

O Nginx do jogo publica somente o shell PWA e encaminha `/api/` e `/ws/` ao
FastAPI. O portal de documentação usa outra imagem, outro document root, a porta
local 8020 e o profile opcional `docs`; ele recebe apenas uma allowlist de HTML,
CSS e SVG sanitizados e não encaminha a API. O fallback do jogo não responde por
rotas de documentação.

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

### ADR-007 — Jogo e portal em imagens separadas

O PWA da porta 8010 não contém documentação, protótipos, Markdown, Swagger ou
OpenAPI. O portal da porta 8020 é opt-in e publica uma allowlist estática. Essa
separação evita que o fallback do jogo masque links quebrados ou exponha
artefatos internos.

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
