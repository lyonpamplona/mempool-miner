# Relatorio de Auditoria das Funcoes Ativas — Mempool Miner

**Data:** 15/08/2026
**Auditoria:** Varredura completa do frontend e backend

---

## 1. RESUMO EXECUTIVO

| Camada | Arquivos | Funcoes | Linhas |
|--------|----------|---------|--------|
| **Frontend** | game.js, index.html, style.css | 48 funcoes JS | 1.467 |
| **Backend** | main.py, ingestor.py, engine.py, storage.py, config.py, events.py, blockchain.py, healthcheck.py | 35 funcoes/classes | ~2.800 |

---

## 2. FRONTEND — 48 FUNCOES ATIVAS

### Audio (2)
- `getAudioContext()` — Cria lazy AudioContext apos interacao do usuario
- `playSound(type)` — Sintetiza sons: tick, success, orphan, buy

### URLs e API (2)
- `leaderboardUrl(realmId)` — Constrói URL REST do leaderboard
- `gameSocketUrl(realmId)` — Constrói URL WebSocket

### Status e Acessibilidade (2)
- `announceGameStatus(message)` — Atualiza aria-live para leitores de tela
- `updateConnectivityStatus(event)` — Detecta online/offline

### PWA (2)
- `showServiceWorkerUpdate()` — Banner de atualizacao
- `registerPwa()` — Registra service-worker.js

### Gerenciamento de Sessao (3)
- `scheduleForSession()` — setTimeout escopado por sessionGeneration
- `cancelSessionTimeout()` — Cancela timeout da sessao
- `teardownSession()` — Limpa WebSocket, timeouts, selecoes, reset UI

### Redes e Catalogo (5)
- `describeNetwork()` — String legivel do status da rede
- `updateNetworkChoice()` — Habilita/desabilita botao conectar
- `getPreferredRealm()` / `savePreferredRealm()` — Persiste em localStorage
- `loadNetworkCatalog()` — Fetch do catalogo de redes

### Modais (1)
- `setModalState()` — Alterna modal com focus trap

### Grade e Layout (2)
- `configureGridSize()` — Calcula tamanho responsivo de celulas
- `initEmptyGrid()` — Cria grade 12x12 com letras aleatorias

### Validacao (2)
- `isValidTransactionEvent()` — Valida contrato de transacao WS
- `isValidLeaderboardPayload()` — Valida resposta do leaderboard

### WebSocket (1 + handlers)
- `startSession()` — Abre WebSocket, configura handlers

### Health e Leaderboard (3)
- `pollNetworkHealth()` — GET health a cada 10s
- `fetchLeaderboard()` — GET leaderboard a cada 10s
- `submitScore()` — POST score apos cada palavra e compra

### Loja (4)
- `updateStoreUI()` — Atualiza estado dos botoes da loja
- `buyHint()` — Custa 5K sats, revela celula inicial
- `buyHardware()` — Custa 100K→500K→2M sats, +10s por nivel
- `buyLightning()` — Custa 1M sats, modo L2 permanente

### Preparacao de Rodada (2)
- `prepareNextBlock()` — Limpa rodada anterior
- `buildPlayableBlock()` — Constrói grade com 6 palavras

### Injecao de Palavras (2)
- `injectWordInGrid()` — Posiciona palavra na grade
- `renderBankWord()` — Cria item no word bank lateral

### Selecao — Pointer (5)
- `getCellFromPoint()`, `handlePointerStart()`, `handlePointerMove()`, `handlePointerEnd()`, `handlePointerCancel()`

### Selecao — Teclado (2)
- `handleGridKeydown()`, `focusGridCell()`

### Logica de Selecao (4)
- `cancelSelection()`, `startSelection()`, `continueSelection()`, `endSelection()`

### Feedback Visual (2)
- `showFloatingText()` — Mostra "+N Sats" sobre a celula
- `drawAnimatedLine()` — Desenha linha SVG entre celulas

### Timer e Resultado (2)
- `startNetworkRace()` — setInterval de 1s
- `showResult()` — Modal de vitoria/derrota

---

## 3. BACKEND — 35 FUNCOES/CLASSES ATIVAS

### API FastAPI (main.py) — 15 endpoints/funcoes
- `healthcheck()` — GET /api/v1/health/live
- `readiness()` — GET /api/v1/health/ready
- `get_networks()` — GET /api/v1/networks
- `get_network_health()` — GET /api/v1/networks/{realm}/health
- `submit_score_v1()` — POST /api/v1/networks/{realm}/leaderboard
- `get_leaderboard_v1()` — GET /api/v1/networks/{realm}/leaderboard
- `submit_score()` — POST /api/leaderboard (alias legado)
- `get_leaderboard()` — GET /api/leaderboard (alias legado)
- `ws_sender()` — Repassa eventos do Redis para WebSocket
- `ws_receiver()` — Detecta desconexao com timeout de 5min
- `serve_websocket()` — Handshake e eventos do realm
- `redis_error_handler()` — Converte falhas Redis em 503
- `get_network_definition()` — Resolve realm no catalogo
- `websocket_origin_allowed()` — Valida origem CORS
- `sanitize_public_event()` — Filtra campos e hash SHA-256 do event_id

### Ingestor (ingestor.py) — 12 funcoes
- `NodeIngestor.__init__()` — Monta dependencias
- `acquire_lease()` — SET NX com TTL para fencing
- `drain_stale_transactions()` — Remove itens da epoch anterior
- `update_status()` — Publica heartbeat e snapshot
- `heartbeat_loop()` — Roda update_status() a cada 10s
- `process_transaction()` — Converte TX e publica evento deduplicado
- `process_transactions()` — Loop de consumo da fila
- `handle_block()` — Avanca epoch, drena backlog, anuncia bloco
- `enqueue_transaction()` — Coloca na fila sem bloquear
- `run()` — Inicia listener, processor, heartbeat
- `close()` — Libera pool HTTP

### Engine (engine.py) — 8 funcoes
- `GameEngine.__init__()` — Carrega NodeConfig
- `_rpc_call()` — JSON-RPC via httpx
- `tx_to_word()` — Double SHA-256 → BIP39
- `get_tx_metadata()` — Palavra, raridade, taxa, vsize
- `get_mempool_size()` — getmempoolinfo
- `get_blockchain_info()` — getblockchaininfo
- `get_best_block_hash()` — getbestblockhash
- `validate_declared_network()` — Verifica chain

### Blockchain (blockchain.py) — 4 funcoes
- `BitcoinZMQListener.__init__()` — Configura socket ZMQ
- `_source()` — Contador monotônico para ordenacao
- `start()` — Conecta ao publisher ZMQ
- `stop()` — Encerra loop de leitura

### Storage (storage.py) — 3 funcoes
- `leaderboard_key()` — Chave namespaced por realm
- `mempool_count_key()` — Chave do contador
- `migrate_legacy_default()` — Copia dados legados

### Config (config.py) — 3 funcoes
- `validate_id_format()` — Regex para IDs
- `NodeConfig.__post_init__()` — Validacoes
- `NodeConfig.from_environment()` — Carrega do ambiente

### Events (events.py) — 2 funcoes
- `utc_now_iso()` — Timestamp UTC
- `event_envelope()` — Campos comuns do protocolo v2

### Healthcheck (ingestor_healthcheck.py) — 1 funcao
- `check()` — Valida token, heartbeat, lease, status

---

## 4. MECANICAS DO META-GAME

### Pontuacao
```
pontos = (500 + comprimento × 50) × combo × tipo_TX × modo_Lightning
```

### Multiplicadores
| Multiplicador | Valor | Condicao |
|---|---|---|
| Combo | +0.5× por acerto em <8s (max 4.0×) | Consecutivo |
| HIGH FEE | ×3 | fee_rate ≥ 20 sat/vb |
| GOLDEN HASH | ×5 | TXID comeca com "00" |
| LIGHTNING | ×10 | Upgrade L2 ativado |

### Loja
| Item | Preco | Efeito |
|---|---|---|
| Dica | 5.000 sats | Revela celula inicial |
| Hardware | 100K→500K→2M sats | +10s por nivel (4 niveis) |
| Lightning | 1.000.000 sats | Grade 8x8, timer 20s, pontos ×10 (permanente) |

### Estados do Jogo
```
TUTORIAL → COLETA DE TX → BUILD GRADE → RODADA ATIVA → RESULTADO → (volta para COLETA)
```

### Persistencia
- **Entre rodadas:** balanceSatoshis, hardwareLevel, networkTimeBonus, isLightningMode, roundNumber
- **Entre sessoes:** mempool-miner-realm (localStorage)
- **Ao trocar de rede:** Tudo reseta

### Leaderboard
- Redis ZADD GT CH (so atualiza se maior)
- Top 10 por realm
- MAX_SCORE = INT32_MAX
- Polling a cada 10s

---

## 5. GAP ANALYSIS — O QUE FALTA

| Funcionalidade proposta | Existe hoje? | Gap |
|---|---|---|
| Leaderboard Epochs (reset a cada 2016 blocos) | NAO | Backend precisa de contador de blocos + reset |
| Lightning Channel Liquidity (dura 5 blocos) | NAO | Lightning e permanente, precisa de contador |
| Slashing (penalidade por erro) | NAO | So zera combo, nao debita saldo |
| MEV Secreto (palavras ocultas) | NAO | Backend nao injeta palavras escondidas |
| Mining Pools (guildas por prefixo) | NAO | Nao existe painel de pools |
| Orphan Block Salvage (RBF) | NAO | Bloco minerado encerra rodada sem opcao de resgate |
