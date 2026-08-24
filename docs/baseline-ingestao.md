# BASELINE — Arquitetura de Ingestão de Transações (Mempool Miner)

Referência do estado atual: onde o código acopla a um nó Bitcoin Core local
(ZMQ + RPC), para a análise de impacto de usar API pública.

## 1. Fluxo de dados completo (passo a passo)

1. **ZMQ rawtx** — `BitcoinZMQListener.start()` conecta socket SUB em
   `tcp://ZMQ_HOST:ZMQ_PORT` e assina `b"rawtx"`/`b"hashblock"`
   (`backend/app/blockchain.py:77-80`); `recv_multipart()` em `:86`;
   topic `rawtx` → `RawTransactionNotice(tx_hex=hexlify(body))` em `:94-103`.
2. **Enfileiramento** — `enqueue_transaction` (`backend/app/ingestor.py:166-170,
   239-249`): `queue.put_nowait((epoch, notice))` em `asyncio.Queue`
   (`:152-154`); fila cheia → descarta e conta (`:243-249`).
3. **Consumo** — `process_transactions` (`ingestor.py:518-541`): `queue.get()`
   → `process_transaction()` → sleep `TX_PROCESS_INTERVAL_SECONDS`.
4. **txid** — double-SHA256 do hex, invertido (`ingestor.py:446-450`).
5. **Metadados** — `engine.get_tx_metadata(txid, tx_hex)` (`ingestor.py:451`;
   `backend/app/engine.py:137-210`); `None` → descarta (`ingestor.py:454-455`).
6. **Eventos globais** — `apply_event_effects` se houver evento ativo no
   Redis (`ingestor.py:461-467`; `engine.py:346-403`).
7. **Contagem mempool** — RPC `get_mempool_size()` fora do lock
   (`ingestor.py:470`; `engine.py:438-448`).
8. **Envelope + dedup + publicação** — sob `epoch_lock` com revalidação de
   epoch (`ingestor.py:475-477`); `event_envelope(action="transaction_received")`
   (`ingestor.py:478-485`; `backend/app/events.py:53-100`); campos em
   `ingestor.py:486-500`; commit via `COMMIT_TRANSACTION_SCRIPT` (Lua):
   checa lease, `SADD dedupe_key(realm, epoch) txid` TTL 3600s (dedup: se
   `SADD==0` não publica), `INCR mempool_count`, `PUBLISH events_channel`
   (`ingestor.py:62-81, 502-514`).
9. **Canal Redis** — `mempool_miner:v2:{realm}:events`
   (`backend/app/storage.py:131-133`).
10. **Relay + WebSocket → frontend** — `EventRelay` (um por realm)
    subscreve o canal (`backend/app/main.py:1884-1895`) e replica cada
    mensagem para as filas dos WebSockets (`main.py:1897-1920`); `ws_sender`
    serializa e envia (`main.py:1953-2007`, `send_text` em `:2000`);
    endpoint `/ws/v1/game/{realm_id}` (`main.py:4862-4865`).
11. **hashblock** — `handle_block` (`ingestor.py:543-615`): `epoch=block_hash`
    (`:561`), `drain_stale_transactions` (`:562, 293-321`), publica
    `block_mined` via `COMMIT_BLOCK_SCRIPT` (`:583-594`), contador de blocos
    (`:599`), block card (`:602`), `update_status` (`:610`).

## 2. O que o BitcoinZMQListener assina e como

- Socket `zmq.SUB` (`blockchain.py:39`), `connect(config.zmq_url)` em `:78`
  (`zmq_url = tcp://{ZMQ_HOST}:{ZMQ_PORT}`, `config.py:173-176, 207`).
- Assinaturas: `SUBSCRIBE b"rawtx"` e `b"hashblock"` (`:79-80`).
- Formato: multipart `[topic, body]` (`:86-92`). `rawtx`: body = bytes da tx
  raw (hexlificado em `:100`); `hashblock`: body = bytes do hash do bloco
  (`:113`). Sem frame de sequência (rawtx envia só 2 frames) — ordenação por
  contador local monotônico (`:45-63`).
- Origem no nó: `zmqpubrawtx`/`zmqpubhashblock` em `tcp://0.0.0.0:28332`
  (`bitcoin/bitcoin.conf:8-9`).

## 3. get_tx_metadata — dependência do nó local

- RPC `getmempoolentry [txid]`, 3 tentativas/backoff 0.5s (`engine.py:165-170`).
- Consome: `vsize` (`:173-175`) e fee: `fees.base` (`:177-178`) com fallback
  para campo `fee` direto quando ausente/zero (Core v0.21+, `:181-184`).
- `fee_rate_sat_vb = fee_btc*1e8/vsize` (`:186`);
  `is_high_fee = fee_rate >= HIGH_FEE_RATE_SAT_VB` (default 20, `:187`,
  `config.py:130`).
- **TX fora do mempool** (`result` não dict): fallback
  `_calculate_vsize_from_hex(tx_hex)` (`:189-192`) — parsing do raw
  (version/inputs/outputs/witness), `weight = base*3 + total`,
  `vsize = weight//4` (`:212-319`). Sem hex → `None`, TX descartada
  (`:193-195`).

## 4. tx_to_word — determinístico e independente do nó

- `engine.py:83-96`: `entropy = bytes.fromhex(txid[:32])` (primeiros 128 bits
  do txid), `Mnemonic("english").to_mnemonic(entropy).split()[0].upper()`.
- Determinístico: função pura do txid + wordlist BIP39 fixa; nenhum dado do
  nó participa. Txid inválido → `"BITCOIN"` (`:94-96`).

## 5. Metadados consumidos pelo jogo (origem de cada campo)

- `is_golden` — `txid.startswith("00")` (`engine.py:159`).
- `is_high_fee` — `fee_rate_sat_vb >= 20` (`engine.py:187`).
- `is_mev` — `int(txid[:8],16) % 100 < 15` (`engine.py:198`).
- `vsize` — `getmempoolentry.vsize` (`:173-175`) ou fallback do hex (`:191`).
- `fee_rate_sat_vb` — `fee*1e8/vsize` (`engine.py:186, 205`).
- `multiplier` — golden 5×, high_fee 3×, combo 15× (`engine.py:321-340, 209`).
- `expand_grid` — `vsize > 1000` (`engine.py:207`).
- `base_reward` — constante 500 (`engine.py:208`).
- Eventos globais: `apply_event_effects` altera `is_golden/is_high_fee/
  multiplier` (`engine.py:346-403`, aplicado em `ingestor.py:461-467`).
- Publicados no evento em `ingestor.py:486-500`.

## 6. Faucet do regtest (bitcoin/entrypoint.sh)

- Inicia `bitcoind` (`:37`), cria wallet `miner` (`:44-49`), gera 150 blocos
  (`:54-62`) e 10 txs iniciais (`:64-72`).
- **Loop contínuo** (`:112-152`): a cada `FAUCET_INTERVAL=20s` envia
  `FAUCET_TXS=12` txs via `sendtoaddress` (`:129-140`); a cada
  `BLOCK_INTERVAL=90s` minera 1 bloco via `generatetoaddress` (`:142-149`).
  Variáveis em `docker-compose.yaml:54-57`.
- **Importância**: regtest não tem tráfego orgânico — o faucet é a ÚNICA
  fonte de transações do jogo (geram os eventos `rawtx`→ZMQ) e de blocos
  (tip fresco, evita IBD, dispara `block_mined`/mudança de epoch).

## 7. Pontos de acoplamento

**(a) ZMQ**
- `blockchain.py:11-12` (import), `:39` (socket SUB), `:77-80` (connect +
  subscribe), `:86` (recv), `:94-116` (dispatch por topic);
  `config.py:125-126, 173-176, 206-207` (ZMQ_HOST/ZMQ_PORT → `zmq_url`);
  `ingestor.py:166-170, 812`; `docker-compose.yaml:173-174, 205-206,
  239-240`; `bitcoin.conf:8-9`.

**(b) RPC JSON do nó local**
- `engine.py:98-135` (`_rpc_call`: POST JSON-RPC em `config.rpc_url` com
  Basic auth/cookie); auth lê `.cookie` de `/home/bitcoin/.bitcoin/...`
  (`engine.py:54-81`).
- Métodos: `getmempoolentry` (`:166`), `getmempoolinfo` (`:444`),
  `getblockchaininfo` (`:457`), `getbestblockhash` (`:466`), validação de
  chain (`:469-540`); config em `config.py:123-124, 168-171, 204-209`;
  chamadores em `ingestor.py:451, 470, 557, 791-793`.

**(c) Nó Bitcoin Core (infra)**
- Serviços `bitcoin-regtest/signet/mainnet` (`docker-compose.yaml:50-85,
  87-122, 124-162`); faucet em `entrypoint.sh` (regtest); gating IBD
  (`ingestor.py:355-357`); validação de chain (`engine.py:501-540`).

## 8. Singleton por realm (realm_id) e troca de fonte

- Cada processo de ingestor serve exatamente 1 `realm_id`
  (`ingestor.py:1-5`); config por env (`config.py:178-214`); um serviço
  `ingestor-*` por realm (`docker-compose.yaml:164-260`).
- Exclusividade via **lease Redis**: `SET NX EX 30` em
  `ingestor_lease_key(realm)` (`ingestor.py:183-190`; `storage.py:166-168`),
  renovação a cada 10s (`:197-237`); todos os commits passam por scripts Lua
  que checam o token da lease (`:62-126, 502-514`).
- **Relação com troca de fonte**: lease/epoch/dedup são ortogonais à fonte.
  Trocar ZMQ+RPC por API pública exige apenas um novo "producer" que
  alimente `enqueue_transaction` (txid+hex ou vsize+fee) e um novo "block
  notifier" para `handle_block` (o epoch = hash do bloco atual precisa vir
  de algum lugar, ex. tip da API). Lease, dedup, Redis PubSub e WebSocket
  permanecem intactos.

## 9. Mapa: dependente do nó local vs independente

**Dependente do nó local (precisa mudar com API pública):**
- Stream ZMQ `rawtx`/`hashblock` — `blockchain.py` inteiro.
- RPCs: `getmempoolentry` (vsize/fee, `engine.py:166`), `getmempoolinfo`
  (mempool_count, `:444`; usado em `ingestor.py:341, 470, 557`),
  `getblockchaininfo` (IBD/blocks/chain, `:457, 500`),
  `getbestblockhash` (epoch inicial, `:466`).
- Auth `.cookie`/RPC user+pass — `engine.py:54-81`, `config.py:208-209`.
- Faucet regtest (fonte de txs) — `entrypoint.sh:112-152`; gating
  IBD/playable — `ingestor.py:355-357`.

**Independente (só precisa de txid + vsize + fee, ou só txid):**
- `tx_to_word` (BIP39 dos 128 bits do txid) — `engine.py:83-96`.
- `is_golden` (prefixo do txid, `:159`); `is_mev` (prefixo do txid, `:198`).
- `fee_rate_sat_vb`/`is_high_fee` (fee+vsize, `:186-187`);
  `expand_grid` (vsize>1000, `:207`); `multiplier`/`base_reward`
  (`:208-209, 321-340`).
- vsize por fallback do hex (sem nó) — `engine.py:212-319`; efeitos de
  eventos globais — `engine.py:346-403`.
- Dedup, epoch, lease, scripts Lua, Redis PubSub, relay WebSocket —
  `ingestor.py`, `storage.py`, `main.py` (sem acoplamento com o nó).

**Conclusão para a análise de impacto**: uma API pública que forneça
`txid` (+ `vsize` e `fee`, ou o hex da tx) cobre todo o cálculo de
metadados; o que ela ainda precisa fornecer é (i) notificação de bloco novo
(para `handle_block`/epoch) e (ii) opcionalmente contagem de mempool e
status de sync (hoje `getmempoolinfo`/`getblockchaininfo`).
