# 04 — Sistemas Transversais e Meta-in-game

Auditoria 100% dos sistemas que atravessam todas as mecânicas do Mempool Miner:
eventos globais, chat, social, arquitetura multi-rede, onboarding, WebSocket e resiliência.
Valores exatos com `path:linha` (estado do código após as Fases 1–8 + auditoria final).

---

## 1. Eventos Globais (`backend/app/global_events.py`)

### 1.1 Tipos, durações e metadados

| Tipo | Valor | Ícone | Cor | Duração | Efeito anunciado |
|---|---|---|---|---|---|
| Fee Spike | `fee_spike` | ⚡ | `#a855f7` | **600s (10 min)** | Todas as palavras High Fee, 3× |
| Golden Rush | `golden_rush` | 🌟 | `#eab308` | **300s (5 min)** | Golden Hash 3× mais frequente, 5× |
| Mempool Flood | `mempool_flood` | 🌊 | `#f97316` | **600s (10 min)** | Grade 15×15 obrigatória, 2× |
| Lightning Storm | `lightning_storm` | ⛈️ | `#0ea5e9` | **180s (3 min)** | Lightning Mode para todos, 10×, 8×8 |

- Enum: `GlobalEventType` — `global_events.py:38-42`
- Metadados (ícone/label/descrição/cor): `EVENT_META` — `global_events.py:46-71`
- Durações: `EVENT_DURATION_SECONDS` — `global_events.py:75-80`
- Aviso antecipado declarado: `EVENT_PREANNOUNCE_SECONDS = 120` — `global_events.py:83`

### 1.2 Scheduler

- Roda em cada instância do backend; lock Redis `SET NX` garante 1 instância por realm — `global_events.py:108-138`
- Chave do lock: `mempool_miner:v2:{realm}:global_event_lock`, TTL = intervalo máximo + 60s — `global_events.py:137-138`
- Intervalo entre eventos: **aleatório 30–60 min** (`min_interval_seconds=1800`, `max_interval_seconds=3600`) — `global_events.py:127-128, 184`
- Ciclo: aguarda → adquire lock → `random.choice` do tipo → pre-anúncio → aguarda → `event_started` → aguarda duração → `event_ended` → libera lock — `global_events.py:181-213, 223-295`
- Erro no ciclo: log + retry em 60s — `global_events.py:176-179`
- Inicialização: `main.py:373-410` (um scheduler por realm, start/stop no lifespan)

### 1.3 Publicação e estado

- Payload publicado no canal Pub/Sub `mempool_miner:v2:{realm}:events` (`events_channel`, `storage.py:131-133`) com `schema_version: 2`, `event_id` = `global_event:{realm}:{type}:{action}`, campos `event_type/label/icon/description/color/preannounced/started_at/ends_at` — `global_events.py:297-336`
- Ações: `event_preannounce`, `event_started`, `event_ended` — `global_events.py:241-248, 262-269, 282-289`
- Estado para consulta rápida: chave `mempool_miner:v2:{realm}:global_event_status`, **TTL 7200s** — `global_events.py:381-389`
- `get_active_event`: lê a chave, expira (e apaga) se `event_ends_at <= now` — `global_events.py:343-378`
- REST: `GET /api/v1/networks/{realm_id}/global-events` → `{realm_id, active_event, event_definitions[4]}` — `main.py:678-711`

### 1.4 Efeitos no jogo — `apply_event_effects`

Local: `backend/app/engine.py:347-403` (staticmethod `GameEngine.apply_event_effects`),
invocado no ingestor a cada transação: `backend/app/ingestor.py:461-467` (falha silenciosa em `ValueError/KeyError/TypeError/RedisError`).

| Evento | Alteração nos metadados da TX |
|---|---|
| `fee_spike` | `is_high_fee = True`; `multiplier = 3.0` (se não golden) ou `15.0` (golden + high fee) — `engine.py:374-383` |
| `golden_rush` | Se não golden e `int(word[:2], 16) % 100 < 30` → `is_golden = True`, `multiplier = 5.0` — `engine.py:385-391` |
| `mempool_flood` | `multiplier *= 2.0` — `engine.py:393-396` |
| `lightning_storm` | `multiplier *= 10.0` — `engine.py:398-401` |

Funções de apoio no backend (definidas, mas a aplicação efetiva de grade/tempo é no frontend — ver 8.4):
- `get_event_grid_size`: lightning=8, flood=15, padrão=12 — `engine.py:406-419`
- `get_event_time_limit`: lightning=20s, flood=base+15s, padrão=base — `engine.py:422-436`

### 1.5 Notificação ao jogador (frontend)

- Estado: `activeGlobalEvent` — `game.js:1249`; `EVENT_META`/`EVENT_DURATION` espelhados — `game.js:1254-1267`
- Banner DOM `#global-event-banner` — `index.html:168-175`; render em `renderGlobalEventBanner` — `game.js:6485-6513` (pre-anúncio mostra "…em breve!", `data-status=preannounce`; ativo seta `body[data-event-active]`)
- Countdown 1s até `event_ends_at` — `game.js:6516-6538`; dismiss manual — `game.js:6558-6560`
- Handlers WS: `event_preannounce/started/ended` → `handleGlobalEventMessage` — `game.js:1743-1754, 6563-6595`; notificações toast "X iniciado!"/"X encerrado." — `game.js:6582-6593`
- Ao iniciar sessão: `loadActiveGlobalEvent()` via REST `global-events` (reconecta o banner se evento já ativo) — `game.js:6598-6627`
- Efeitos na rodada: `buildPlayableBlock` sobrepõe grade/tempo/multiplicador — `game.js:2311-2348`:
  - `lightning_storm` → grade 8, tempo 20s, `globalRewardMultiplier = 10`
  - `mempool_flood` → grade 15, tempo 75s+bonus, `globalRewardMultiplier = 2`
  - `fee_spike` → `globalRewardMultiplier = 3` (grade segue regra vsize)
  - `golden_rush` → `globalRewardMultiplier = 5`
  - Aplicado em `effectiveBaseReward = floor(baseReward * halvingFactor * globalRewardMultiplier)` — `game.js:2348`

---

## 2. Chat / Comms (aba SOCIAL → CHAT)

### 2.1 Backend

- Endpoints: `POST /api/v1/networks/{realm_id}/chat/send` — `main.py:2384-2416`; `GET /api/v1/networks/{realm_id}/chat/history` — `main.py:2419-2442`
- Limites exatos — `main.py:2300-2311`:
  - `CHAT_MAX_PER_MINUTE = 5` (rate limit por jogador)
  - `CHAT_MAX_CHARS = 100`
  - `CHAT_RATE_TTL = 60` (janela em segundos)
  - `CHAT_BANNED_WORDS = {spam, scam, hack, phish, ban, kill, death, hate, abuse, racist, sexist, toxic}` (substring, case-insensitive) — `main.py:2300-2303, 2341-2354`
  - `CHAT_EMOJIS = [🪙, ⛏️, ₿, 📡, 🔗, ⚡, 💎, 🏆]` — `main.py:2306`
- Rate limit: chave `chat_rate_key` (`mempool_miner:v2:{realm}:chat_rate:{username}`, `storage.py:245`), contador com TTL 60s; excedeu → **HTTP 429** "Limite de mensagens excedido. Aguarde 1 minuto." — `main.py:2323-2338, 2408-2409`
- Moderação violada → **HTTP 400** "Mensagem contém conteúdo inadequado" — `main.py:2404-2405`
- Persistência: `LPUSH` em `chat_messages_key` (`mempool_miner:v2:{realm}:chat_messages`, `storage.py:240`) + `LTRIM 0 49` → **mantém apenas as últimas 50 mensagens por realm** (sem TTL na lista) — `main.py:2357-2381`
- Envelope: `{action: "chat_message", username, message, timestamp(ISO UTC)}` — `main.py:2371-2376`

### 2.2 Frontend

- Painel: `#chat-panel` (mensagens, input, botão ENVIAR, barra de emojis, `#chat-rate-info`) — `index.html:448-460`
- `CHAT_MAX_MESSAGES = 50` (teto local) — `game.js:4223`
- Histórico: `loadChatHistory()` busca **20** mensagens ao abrir a aba SOCIAL (uma vez por sessão; `chatHistoryLoaded`/`chatHistoryLoading`) — `game.js:4277-4306, 1303-1305`
- Envio: `sendChatMessage()` via `fetch` POST; sucesso → append local; 429 → "Limite atingido. Aguarde 1 min." + botão desabilitado — `game.js:4413-4465, 4396-4406`
- Emojis: barra gerada a partir de `CHAT_EMOJIS`-like local, insere token no cursor — `game.js:4243-4254, 4469-4476`
- Reset do chat no teardown da sessão — `game.js:4503-4508`

### 2.3 O que funciona / o que não funciona

- ✅ Persistência em Redis (últimas 50) e histórico via REST.
- ✅ Rate limit + moderação por palavra.
- ❌ **Sem broadcast em tempo real**: `chat_message` NÃO está em `PUBLIC_EVENT_FIELDS` (`main.py:97-189`) e o backend **não publica** a mensagem no canal `events` — o jogador só vê as próprias mensagens (resposta do POST) e o histórico carregado ao abrir a aba. Mensagens de outros jogadores só aparecem se a aba for reaberta. Ver **8.2**.

---

## 3. Social (Amigos / Ranking social)

### 3.1 Amigos (implementado)

- Endpoints — `main.py`:
  - `POST /api/v1/networks/{realm_id}/friends/add` — `main.py:4309-4341` (rejeita auto-add; `SADD` em `friends_key`)
  - `POST /api/v1/networks/{realm_id}/friends/remove` — `main.py:4344-4367`
  - `GET /api/v1/networks/{realm_id}/friends/{username}` — `main.py:4401-4414`
- Armazenamento: `friends_key` = `mempool_miner:v2:{realm}:friends:{username}` (Redis SET) — `storage.py:340-342`
- Lista com status: `_get_friends_list` — `main.py:4370-4398`:
  - `online` via hash `online_key` (`mempool_miner:v2:{realm}:online`, `storage.py:345-347`)
  - `level` via `_get_player_level`
  - **`co_op_bonus = min(online_count * 0.05, 0.20)`** → +5% por amigo online, teto +20% (4 amigos) — `main.py:4388-4390`
- Frontend: aba SOCIAL → seção EQUIPE (`#friends-panel`) — `index.html:462-474`;
  `loadFriendsList`/`renderFriendsUI`/`addFriend`/`removeFriend` — `game.js:6878-7040`; inicializador de sessão `'friends'` — `game.js:7055-7056`; exibe "Bônus Co-op: +X% (N online)" — `game.js:6901-6908`

### 3.2 Status online (Fase 11)

- Heartbeat do jogador via WS: cliente responde `player_heartbeat` → backend grava `hset(online_key, username, now)` + `expire 86400` — `main.py:2029-2042`
- Frontend responde ao `heartbeat` do servidor — `game.js:1779-1785`

### 3.3 Implementado vs placeholder

| Item | Estado |
|---|---|
| Adicionar/remover amigo (unidirecional, por username) | ✅ Implementado |
| Status online/offline por amigo | ✅ Implementado (heartbeat WS) |
| Nível do amigo na lista | ✅ Implementado |
| Bônus co-op (+5%/amigo online, máx 20%) | ⚠️ **Calculado e exibido, mas NUNCA aplicado a recompensas/score** (ver 8.3) |
| Pedido de amizade / aceitação mútua | ❌ Não existe (add é imediato e unilateral) |
| Amizade cross-realm | ❌ Não existe (chave por realm) |
| Ranking social (amigos no leaderboard) | ❌ Não existe — o leaderboard é global por realm (`leaderboard_key`, `storage.py:141-143`); não há visão "seus amigos no ranking" |
| Chat em tempo real entre amigos | ❌ Ver 8.2 |

---

## 4. Arquitetura Multi-rede (regtest / signet / mainnet)

### 4.1 Catálogo

`backend/app/config.py:56-66` (`NETWORK_CATALOG`):

| realm_id | Rede | node_id | Label | `optional` |
|---|---|---|---|---|
| `regtest` | regtest | `regtest-local` | "Regtest local" | não |
| `signet` | signet | `signet-public` | "Signet pública" | não |
| `mainnet` | mainnet | `mainnet-pruned` | "Mainnet podada" | **sim** |

- `BitcoinNetwork` (regtest/signet/mainnet; `rpc_chain` = "main" p/ mainnet) — `config.py:19-37`
- `DEFAULT_REALM_ID` = realm padrão do backend (env) — `main.py:92`
- O que cada rede oferece ao jogador: **a mesma mecânica completa** (mesmo jogo, mempool real da rede); a diferença é a origem das transações/blocos e o estado de sincronização. Mainnet é opcional: sem heartbeat → status `disabled` ("Mainnet desativada. Inicie o profile mainnet para habilitar.") — `main.py:624-625`, `game.js:749`

### 4.2 Estado `playable` e IBD gating

- Ingestor: `update_status()` a cada **10s** (`heartbeat_loop`) — `ingestor.py:410-428`
  - `status = "syncing" if initialblockdownload else "ready"`; **`playable = not in_ibd`** — `ingestor.py:355-357`
  - RPC indisponível → `status = "unavailable"`, `playable = False` — `ingestor.py:349-352`
  - Snapshot commitado atomicamente (Lua) em `node_status_key` + `realm_state_key`; evento `network_status` publicado **somente quando o status muda** — `ingestor.py:359-406`
- API: `network_snapshot()` — `main.py:612-648`:
  - **`playable = observed.playable AND has_live_heartbeat AND runtime_status == "ready"`** — `main.py:633-635`
  - Status públicos: `starting, syncing, ready, unavailable, stopped, disabled` — `main.py:94-96`
  - Campos: `realm_id, network, display_name, status, playable, initial_block_download, verification_progress, pruned` — `main.py:636-645`
- Gating de pontuação: `submit_score_for_realm` exige `playable`, senão **HTTP 409** "Rede indisponivel para pontuacao" — `main.py:763-765`
- Gating de transações: ingestor descarta TX se `not self.playable` — `ingestor.py:443, 476`

### 4.3 Como o jogador troca de rede

- Catálogo: `GET /api/v1/networks` → `{schema_version: 2, default_realm_id, networks[]}` — `main.py:714-726`; health por rede: `GET /api/v1/networks/{realm_id}/health` — `main.py:729-740`
- Frontend:
  - `loadNetworkCatalog()` — `game.js:786-860`: popula `<select id="network-select">`; **opção desabilitada se `!playable`** (`game.js:825`); retry a cada **10s** enquanto houver rede `starting/syncing/unavailable` (`game.js:839-843`)
  - Preferência persistida em `localStorage["mempool-miner-realm"]` — `game.js:769-784`; seleção: preferida playable → default → primeira playable — `game.js:829-836`
  - Botão **TROCAR REDE** (footer) — `index.html:522`; handler: `teardownSession('user-network-change')` + modal auth + `loadNetworkCatalog()` — `game.js:1327-1334`
  - `updateNetworkChoice()`: desabilita "EXECUTE_NODE" se a rede escolhida não for playable — `game.js:763-767`
  - `describeNetwork()`: mensagens por status (disabled/unavailable/stopped/syncing+progresso%/playable) — `game.js:747-761`
  - Fallbacks em `startSession()`: (1) recarrega catálogo, (2) primeira rede playable, (3) força `signet` — `game.js:1416-1443`
  - Troca de realm zera estado local: `balanceSatoshis = 0; hardwareLevel = 1; roundNumber = 1` — `game.js:1468-1477`

---

## 5. Onboarding

### 5.1 Primeiro acesso

- Boot: tenta restaurar sessão de `sessionStorage["mempool-miner-session"]` — `game.js:1364-1404`
  - **Sem sessão salva → abre `#auth-modal`** (comentário no código diz "modal de tutorial", mas é apenas o modal de autenticação — `game.js:1396-1398`)
- Modal `SYSTEM_AUTHENTICATION` — `index.html:529-544`:
  - Seleção de rede (com status ao vivo em `#network-status`)
  - `OPERATOR_ID`: input `maxlength=16`; sanitização no `startSession` mantém `[letras/números/_-]` e **corta em 12 chars**; vazio → `Miner_` + aleatório 0–9998 — `game.js:1445-1455`
  - `POOL / GUILDA (OPCIONAL)`: `maxlength=20`, sanitizado a 20 — `game.js:1450-1454`
  - Botão `EXECUTE_NODE` (submit do form) — `index.html:540-542`, `game.js:1270-1273`
- **Não há tutorial passo a passo** (nenhum walkthrough, dica contextual ou primeira rodada guiada). O onboarding é: escolher rede → nome → jogar.

### 5.2 Estado inicial do jogador

| Campo | Valor inicial | Fonte |
|---|---|---|
| Saldo | **0 sats** | `game.js:344` (`balanceSatoshis = 0`); backend: `balance: 0` — `main.py:895` |
| Hardware | **nível 1** ("CPU Miner"; upgrades: 100.000 / 500.000 / 2.000.000 sats) | `game.js:345-347`; backend `hardware_level: 1` — `main.py:896` |
| Nível/XP | não há sistema de nível no estado base (nível aparece via stats/achievements) | `main.py:893-903` |
| Combo | `combo_multiplier: 1.0` | `main.py:899` |
| Lightning | inativo, 0 blocos | `main.py:897-898` |
| Energia | **10/10** (inicializada no primeiro `GET /energy/status`); regen 1 a cada **1800s (30 min)**; compra: **2000 sats por 3 energia** | `main.py:4421-4424, 4455-4469` |
| Estado persistido | `player_state_key` = `mempool_miner:v2:{realm}:player:{username}` | `storage.py:189-191` |
| Sessão local | `sessionStorage` (minerName, realm, saldo, hardware, rodada, lightning, combo) | `game.js:309-339` |

- Reconciliação ao carregar: backend é fonte de verdade, mas o frontend **nunca apaga saldo local maior** (toma o máximo e faz `syncPlayerState`) — `game.js:2044-2076`

---

## 6. WebSocket — eventos recebidos pelo frontend

Endpoint: `WS /ws/v1/game/{realm_id}` (legado: `/ws/game`) — `main.py:4862-4871`; URL construída em `game.js:259-264`.
Handshake: valida origem (CORS) e realm; envia `game_start` com snapshot; depois fan-out via `EventRelay` (fila por conexão, **maxsize 1000**) — `main.py:2045-2134, 1852-1943`.
Contrato público: `PUBLIC_EVENT_FIELDS` — `main.py:97-189` (campos por ação; `event_id` virado SHA-256 opaco — `main.py:550-577`).

| `action` | Campos públicos | Efeito na UI (game.js) |
|---|---|---|
| `game_start` | status, playable, initial_block_download, verification_progress, pruned | Handshake: `sessionReady = playable`; se false → overlay + modal + retry catálogo 10s; se true → inicia polling (leaderboard 10s, pools 15s, health 10s) e `prepareNextBlock()` — `game.js:1574-1610` |
| `network_status` | idem | Atualiza `#ui-node-status`; `playable=false` → teardown + overlay + catálogo — `game.js:1611-1621` |
| `transaction_received` | word, txid, tx_stub, is_golden, is_high_fee, vsize, fee_rate_sat_vb, is_mev, expand_grid, base_reward, multiplier | Enche `txBuffer` (dedup por palavra; troca de epoch zera buffer; roteia p/ boss se ativo); com `WORDS_PER_BLOCK` palavras → agenda build em 500ms — `game.js:1634-1662` |
| `block_mined` | block_hash, mempool_count, discarded_backlog, is_halving_block | Dedup por hash/epoch; flash de halving; credita card do bloco; encerra sprint; oferece Orphan Salvage; decrementa Lightning; `prepareNextBlock()` — `game.js:1663-1726` |
| `leaderboard_reset` | realm_id, epoch | "Nova temporada!" + refetch do leaderboard + tracking — `game.js:1728-1734` |
| `market_sale` | listing_id, seller, buyer, powerup_id, price, seller_earnings | Se o vendedor é o jogador: recarrega mercado/inventário/estado + toast — `game.js:1623-1632` |
| `boss_block` | block_count, boss_hp, boss_grid_size, boss_words, boss_timer, boss_reward_multiplier, boss_loot | `handleBossBlock` — `game.js:1736-1739` |
| `event_preannounce` / `event_started` / `event_ended` | event_type, event_label, event_icon, event_description, event_color, event_preannounced, event_started_at, event_ends_at | Banner global + countdown + toasts — `game.js:1743-1754, 6563-6595` |
| `pvp_challenge` / `pvp_start` / `pvp_score_update` / `pvp_end` / `pvp_timer` | (campos PvP) | Toasts de desafio/início/fim; **`pvp_score_update` e `pvp_timer` têm handlers vazios** — `game.js:1757-1776` |
| `heartbeat` | (vazio) | Cliente responde `player_heartbeat` (status online) — `game.js:1779-1785` |

Extras:
- Eventos de outro realm são ignorados; `game_start` de realm divergente fecha com **4001** — `game.js:1560-1573`
- Epoch divergente em `block_mined` → fecha com **4003** e reconecta em 1s — `game.js:1788-1807`
- Heartbeat do servidor a cada **30s** de inatividade — `main.py:1953-2007`

---

## 7. Resiliência

### 7.1 Backend fora do ar

- `onclose` → `teardownSession('socket-close')` + overlay "Reconectando..." — `game.js:1505-1524`
- **Retry com backoff exponencial**: `maxReconnectAttempts = 5`, `baseDelay = 1000ms`, `delay = 1000 × 2^(n-1)` (1s, 2s, 4s, 8s, 16s); após 5 falhas → "Falha na reconexão. Recarregue a página." — `game.js:1526-1543`
- Códigos que **não** reconectam: **1008** (origem/rede inválida), **4001** (realm divergente), **4002** (timeout de handshake) → "Use Trocar rede para reconectar." — `game.js:1512-1518`
- Timeout de handshake: **10s** sem `game_start` → `socket.close(4002)` — `game.js:1493-1495`
- Sucesso de `game_start` zera `reconnectAttempt` — `game.js:1578`

### 7.2 WebSocket desconectado / inativo

- Receiver do servidor: timeout de **300s** sem mensagem do cliente → encerra (evita conexões órfãs) — `main.py:2010-2026`
- Heartbeat do servidor (30s) permite ao cliente detectar inatividade; expiração detectada → `teardownSession('heartbeat-expired')` — `game.js:1813-1835`
- Fila do relay cheia (1000) → evento descartado com warning (backpressure) — `main.py:1905-1913`
- Relay é criado no 1º cliente e destruído no último (contador `_relay_connections`) — `main.py:1846-1849, 2126-2133`

### 7.3 Rede do navegador / PWA

- `navigator.onLine` → `updateConnectivityStatus`: offline desabilita catálogo ("Sem conexão") e avisa "Redes, eventos e ranking exigem conexão." — `game.js:620-638, 795-804`
- Ao voltar online: recarrega catálogo se o modal de auth estiver aberto — `game.js:631-637`
- PWA/service worker registrado com atualização sob decisão do jogador — `game.js:652-719`
- `pagehide` salva sessão; `pageshow` (bfcache) re-dispara inicializadores dos painéis — `game.js:1347-1360`
- Polling de saúde da rede a cada 10s durante a sessão — `game.js:1598-1608, 1815+`

---

## 8. Pontas soltas

| # | Severidade | Ponto solto | Evidência |
|---|---|---|---|
| 8.1 | **ALTA** | **Timing do pre-anúncio de eventos globais está quebrado.** O pre-anúncio é publicado **no mesmo instante** do trigger (`_publish_event` em `global_events.py:241-248`), não 2 min antes do início. O scheduler então aguarda `duration - 120s` e só aí publica `event_started` (`global_events.py:257-269`). Consequências: (a) a janela de pre-anúncio é `duration-120s` (ex.: 8 min no Fee Spike, 1 min no Lightning Storm), não 2 min; (b) `started_at`/`ends_at` no payload não batem com o início/fim reais — o evento real termina em `t + 2×duration − 120s`, mas `event_ends_at = t + duration`; (c) o countdown do frontend (`game.js:6516-6538`) zera **antes** do evento realmente acabar, e o `event_ended` chega depois; (d) o backend aplica efeitos desde `t=0` (status key setada no pre-anúncio, `global_events.py:334`), ou seja, os efeitos começam a valer antes do banner mostrar "ativo". | `global_events.py:223-295` vs docstring `global_events.py:114-121` ("Pre-anuncia 2 minutos antes") |
| 8.2 | **ALTA** | **Chat não é entregue em tempo real.** `chat_message` não existe em `PUBLIC_EVENT_FIELDS` (`main.py:97-189`) e `_store_chat_message` só faz `LPUSH` no Redis (`main.py:2357-2381`) — nunca publica no canal `events`. O frontend só renderiza a própria mensagem (resposta do POST, `game.js:4445-4448`) e o histórico de 20 msgs ao abrir a aba (`game.js:4277-4306`). Dois jogadores na mesma aba SOCIAL **não veem as mensagens um do outro** em tempo real. | `main.py:97-189, 2357-2381`; `game.js:4413-4465` |
| 8.3 | **ALTA** | **Bônus co-op de amigos é anunciado mas nunca aplicado.** `co_op_bonus = min(online_count × 0.05, 0.20)` é calculado no backend (`main.py:4388-4390`) e exibido na UI ("Bônus Co-op: +X%", `game.js:6901-6908`), mas nenhum cálculo de recompensa/score consome esse valor — a mecânica é cosmética. | `main.py:4388-4390`; ausência de uso em `submit_score_for_realm` (`main.py:743-787`) e no frontend |
| 8.4 | **MÉDIA** | **Golden Rush pode falhar silenciosamente por palavra.** `int(tx_metadata.get("word", "A")[:2], 16)` (`engine.py:388`) lança `ValueError` quando os 2 primeiros caracteres da palavra não são hexadecimais (ex.: "CHAVE" → "CH"); o `try/except` do ingestor (`ingestor.py:466-467`) engole o erro e a TX segue sem o efeito. Ou seja: a frequência 3× só vale para palavras cujo prefixo é hex. | `engine.py:385-391`; `ingestor.py:466-467` |
| 8.5 | **MÉDIA** | **PvP: handlers vazios no frontend.** `pvp_score_update` e `pvp_timer` têm handlers vazios (`game.js:1757-1776`) — o jogador não vê placar/tempo do PvP ao vivo. | `game.js:1757-1776` |
| 8.6 | **BAIXA** | **Onboarding sem tutorial.** O comentário "modal de tutorial" (`game.js:1396-1398`) é enganoso — é apenas o modal de autenticação; não há walkthrough nem primeira rodada guiada. | `game.js:1364-1404` |
| 8.7 | **BAIXA** | **Mainnet opcional desativada por padrão** — sem heartbeat do profile mainnet, a rede aparece `disabled` e o jogador não pode jogar nela. | `main.py:624-625` |
