# Relatório — Viabilidade de API Pública de Dados Bitcoin no Mempool Miner

**Data:** 2026-08-23
**Método:** 3 subagentes em paralelo — (1) pesquisa online + testes ao vivo da API do mempool.space, (2) pesquisa online + testes ao vivo da API da Blockstream e alternativas, (3) leitura do código para mapear a arquitetura atual (baseline).
**Objetivo:** estudar a possibilidade de usar API pública para **receber transações, decodificá-las e gerar as palavras** do jogo, e o impacto no Mempool Miner.
**Status:** apenas análise — nenhuma mudança aplicada.

---

## 1. Resumo Executivo (veredito)

**É viável e o impacto é contido.** A arquitetura atual foi desenhada de forma que a lógica do jogo é **agnóstica à fonte de dados**: a palavra é derivada deterministicamente do **TXID** (BIP39 dos 128 primeiros bits), e os metadados (vsize, fee, fee_rate) são campos que **qualquer API pública já entrega prontos**.

- O que **precisa mudar**: apenas o "producer" — o `BitcoinZMQListener` (ZMQ) + as chamadas RPC `getmempoolentry`/`getmempoolinfo`/`getblockchaininfo`/`getbestblockhash`.
- O que **permanece intacto**: `tx_to_word`, cálculo de raridade/multiplicador, dedup, epoch, lease, scripts Lua, Redis PubSub, relay WebSocket, frontend.
- **Regtest continua com nó local + faucet** (não existe API pública de regtest). Signet e mainnet **podem** usar API pública.
- **Recomendação:** manter o nó local como fonte primária (zero custo, zero limite, latência mínima) e usar a API pública como **fallback/backup** e para **dev/testes** — ou substituir signet/mainnet por API pública se quiser eliminar a infra de nós nessas redes.

**Esforço estimado:** baixo a médio (1–3 dias) para um "producer" de API pública plugável, sem tocar na lógica do jogo.

---

## 2. Arquitetura atual (baseline)

> Documento completo: `docs/baseline-ingestao.md`

### 2.1 Fluxo de dados (hoje)

```
Nó Bitcoin Core (ZMQ rawtx/hashblock)
   │  BitcoinZMQListener (blockchain.py) — socket SUB, assina b"rawtx"/b"hashblock"
   ▼
enqueue_transaction (ingestor.py) — asyncio.Queue
   ▼
process_transactions → process_transaction
   │  txid = double-SHA256(hex) invertido
   │  engine.get_tx_metadata(txid, tx_hex)  ← RPC getmempoolentry (vsize, fee)
   │  engine.tx_to_word(txid)               ← BIP39 dos 128 bits do txid
   ▼
COMMIT_TRANSACTION_SCRIPT (Lua) — checa lease, SADD dedup, PUBLISH events_channel
   ▼
Redis PubSub (mempool_miner:v2:{realm}:events)
   ▼
EventRelay → WebSocket → frontend
```

### 2.2 O que é **dependente do nó local** (precisaria mudar)

| Componente | Onde | O que faz |
|---|---|---|
| Stream ZMQ `rawtx`/`hashblock` | `blockchain.py` inteiro | Fonte de transações e blocos |
| RPC `getmempoolentry` | `engine.py:166` | vsize + fee da tx |
| RPC `getmempoolinfo` | `engine.py:444` | contagem do mempool |
| RPC `getblockchaininfo` | `engine.py:457` | IBD / blocks / chain (gating playable) |
| RPC `getbestblockhash` | `engine.py:466` | epoch inicial |
| Auth `.cookie`/user+pass | `engine.py:54-81` | autenticação RPC |
| Faucet regtest | `entrypoint.sh:112-152` | fonte contínua de txs (regtest) |

### 2.3 O que é **independente** (só precisa de txid + vsize + fee)

- `tx_to_word` (BIP39 dos 128 bits do txid) — `engine.py:83-96`
- `is_golden` (prefixo `00` do txid), `is_mev` (prefixo do txid)
- `fee_rate_sat_vb` / `is_high_fee` (fee + vsize), `expand_grid` (vsize>1000)
- `multiplier` / `base_reward`
- vsize por fallback do hex (sem nó) — `engine.py:212-319`
- **Dedup, epoch, lease, scripts Lua, Redis PubSub, relay WebSocket** — `ingestor.py`, `storage.py`, `main.py` (sem acoplamento com o nó)

### 2.4 Insight-chave

> **A palavra do jogo é uma função pura do TXID.** Não importa quem fornece o txid (nó local, mempool.space, Blockstream) — a palavra gerada é **idêntica**. Isso torna o jogo **agnóstico à fonte de dados** e é o que torna a troca de fonte de baixo impacto.

O que a API pública ainda precisa fornecer além de `txid+vsize+fee`:
1. **Notificação de bloco novo** (para `handle_block`/mudança de epoch) — o epoch é o hash do bloco atual.
2. **Opcional:** contagem de mempool e status de sync (hoje `getmempoolinfo`/`getblockchaininfo`).

---

## 3. APIs públicas pesquisadas (testes ao vivo)

### 3.1 mempool.space — **melhor opção**

**Fonte:** [docs REST](https://mempool.space/docs/api/rest) · [docs WebSocket](https://mempool.space/docs/api/websocket) · [signet](https://mempool.space/signet/docs/api/rest) · [Enterprise](https://mempool.space/enterprise) · [ToS](https://mempool.space/terms-of-service)

**REST (mainnet):**

| Endpoint | O que retorna | Teste ao vivo |
|---|---|---|
| `GET /api/mempool` | `count`, `vsize`, `total_fee`, `fee_histogram` | ✅ `count=76958` |
| `GET /api/mempool/recent` | **Últimas 10 txs** com `txid`, `fee`, `vsize`, `value` | ✅ |
| `GET /api/tx/:txid` | `fee`, `weight`, `size`, `vin`, `vout`, `status` | ✅ 200 em 0,66s |
| `GET /api/mempool/txids` | Lista completa de txids (~5 MB) | ⚠️ pesado, evitar em loop |

**WebSocket (tempo real) — `wss://mempool.space/api/v1/ws`:**

- `{"track-mempool": true}` → evento `mempool-transactions` com `added`/`removed`/`mined`/`replaced`. Cada tx em `added` tem **`txid`, `fee`, `vsize`, `feePerVsize`, `firstSeen`, `status`** — ou seja, **txid + vsize + fee_rate em tempo real, sim**.
- `{"track-mempool-txids": true}` → só txids (baixa banda; a doc recomenda para uso não-empresarial).
- `{"track-mempool-block": 0}` → bloco projetado com deltas.
- **Teste ao vivo:** handshake OK, ~1 evento/s, primeiro evento em ~0,6–0,8s.

**Redes:** mainnet ✅ · **signet ✅** (`mempool.space/signet/api/...` + `wss://mempool.space/signet/api/v1/ws`, testado ao vivo) · testnet3 (deprecado).

**Rate limit / SLA:**
- Limites **não divulgados**; 429 e **banimento de IP** por excesso; sem API key no tier gratuito.
- ToS **"AS IS, AS AVAILABLE"** — sem SLA no tier gratuito (99,9% só no Enterprise, preço sob consulta).
- Mantenedor recomenda nó próprio para aplicações que dependem da API.
- **Open source e self-hostável** (fallback definitivo).

**Latência:** ~1–5s (propagação P2P + ingestão deles) vs. ms do ZMQ local. **Irrelevante para caça-palavras.**

**Pegadinhas:**
- `/api/tx/:txid` **não** traz `vsize`/`fee_rate` prontos → calcular `vsize = weight/4`, `fee_rate = fee/vsize`.
- Frames WS do cliente precisam ser mascarados (RFC 6455) — bibliotecas padrão fazem isso.
- Mempool do serviço ≠ mempool global (visão dos nós deles).
- RBF: txs substituídas saem (`replaced`/`removed`) — tratar palavra "invalidada".

### 3.2 Blockstream (api.blockstream.info)

**Fonte:** [docs](https://developer.blockstream.com/api/) · testes ao vivo nesta sessão

**REST:**

| Endpoint | O que retorna | Teste ao vivo |
|---|---|---|
| `GET /api/mempool/recent` | **`txid`, `fee`, `vsize`, `value`** (últimas txs) | ✅ mainnet + signet + testnet |
| `GET /api/tx/:txid` | `fee`, `weight`, `vsize`, `vin`, `vout`, `status` | ✅ 200 |

- **Signet:** `https://blockstream.info/signet/api/...` ✅ (testado)
- **Testnet:** `https://blockstream.info/testnet/api/...` ✅
- **Rate limit:** 5 chamadas rápidas → todas HTTP 200 (limite tolerante; não observado 429).
- **Tempo real:** via **protocolo Electrum** (WebSocket `wss://blockstream.info:50002` ou `electrum.blockstream.info`), com `mempool.subscribe` — menos "pronto" que o WS nativo do mempool.space.

**Veredito:** Blockstream entrega `txid+fee+vsize` via REST (basta polling de `/mempool/recent` a cada 1–2s) e tem signet/testnet. O tempo real é via Electrum (mais verboso que o WS nativo do mempool.space). Boa opção secundária.

### 3.3 Alternativas

- **Bitaps** — bloqueado por Cloudflare no teste; API paga, foco em ledger.
- **blockchain.com API** — REST, sem WebSocket de mempool em tempo real; rate limit agressivo.
- **Self-hosted mempool** — subir sua própria instância do mempool.space (open source, Docker) elimina dependência de terceiro e rate limits; custo de infra.

---

## 4. Análise de impacto no Mempool Miner

### 4.1 O que muda (o "producer")

| Atual (nó local) | Com API pública |
|---|---|
| `BitcoinZMQListener` (ZMQ SUB `rawtx`/`hashblock`) | Cliente WS do mempool.space (`track-mempool`) **ou** polling REST de `/mempool/recent` (Blockstream) |
| RPC `getmempoolentry` (vsize+fee) | **Desnecessário** — a API já entrega `vsize`+`fee` (mempool.space WS traz `feePerVsize` pronto) |
| RPC `getmempoolinfo` (contagem) | `GET /api/mempool` (mempool.space) ou `count` do WS |
| RPC `getblockchaininfo` (IBD/playable) | Status da API / `track-mempool-block` |
| RPC `getbestblockhash` (epoch) | Hash do bloco via `mined`/`track-mempool-block` |
| Auth `.cookie`/RPC | **Desnecessário** (API pública, sem auth no tier gratuito) |

### 4.2 O que permanece intacto

- `tx_to_word` (BIP39) — **idêntico** para qualquer fonte
- Cálculo de raridade/multiplicador (`is_golden`, `is_high_fee`, `is_mev`, `expand_grid`, `multiplier`)
- Dedup (`COMMIT_TRANSACTION_SCRIPT`), epoch, lease, scripts Lua
- Redis PubSub, `EventRelay`, WebSocket, frontend
- **Faucet regtest** (regtest continua com nó local)

### 4.3 Esforço estimado

| Tarefa | Esforço |
|---|---|
| Cliente WS do mempool.space (producer) | 0,5–1 dia |
| Mapear campos da API → `get_tx_metadata` (vsize/fee/fee_rate) | 0,5 dia |
| Notificador de bloco (epoch) via `mined`/`track-mempool-block` | 0,5 dia |
| Fallback/healthcheck (API caiu → voltar pro nó local) | 0,5 dia |
| Testes (signet ao vivo) | 0,5 dia |
| **Total** | **~2–3 dias** |

### 4.4 Riscos e mitigações

| Risco | Severidade | Mitigação |
|---|---|---|
| Rate limit / 429 / ban de IP | Média | Usar WS (1 conexão) em vez de polling agressivo; `track-mempool-txids` (baixa banda); manter nó local como fallback |
| API cai (sem SLA gratuito) | Média | Fallback automático para nó local; ou self-hosted mempool |
| Latência ~1–5s | Baixa | Irrelevante para caça-palavras |
| RBF invalida palavra | Baixa | Tratar `replaced`/`removed` (palavra "queimada") |
| Mempool do serviço ≠ global | Baixa | Aceitável para jogo; cross-check com nó local |
| Dependência de terceiro | Média | Self-hosted mempool (open source) como plano B |

---

## 5. Opções de implementação

### Opção A — **API pública como fallback/backup** (recomendada)
- Mantém nó local + ZMQ como fonte primária.
- Adiciona cliente WS do mempool.space como **fallback** (se o ZMQ ficar mudo) e para **cross-check** de txids.
- **Impacto:** mínimo, aditivo. Não muda o comportamento atual.
- **Esforço:** ~1–2 dias.
- **Quando:** se quiser resiliência sem arriscar a fonte primária.

### Opção B — **Substituir signet/mainnet por API pública**
- Signet e mainnet usam API pública (mempool.space WS); regtest continua com nó local + faucet.
- **Impacto:** elimina a infra de nós signet/mainnet (economia de recursos), mas adiciona dependência de terceiro.
- **Esforço:** ~2–3 dias.
- **Quando:** se quiser simplificar a infra e aceitar a dependência.

### Opção C — **Híbrido plugável (fonte configurável por realm)**
- Abstrai o "producer" em uma interface; cada realm escolhe a fonte (nó local, mempool.space, Blockstream) via config/env.
- **Impacto:** maior refatoro, mas máxima flexibilidade.
- **Esforço:** ~3–5 dias.
- **Quando:** se quiser a arquitetura mais limpa e futura.

---

## 6. Recomendação

1. **Curto prazo:** **Opção A** — adicionar o WS do mempool.space como fallback/backup. Baixo risco, alto valor (resiliência + cross-check), não toca na lógica do jogo.
2. **Médio prazo:** avaliar **Opção B** para signet (testar o pipeline completo contra `mempool.space/signet` sem mainnet).
3. **Longo prazo:** se a dependência de terceiro for aceitável, **Opção C** (fonte plugável por realm) é a arquitetura mais limpa.

**Próximo passo (se você aprovar):** implementar a Opção A — um `PublicApiIngestor` (cliente WS do mempool.space) que alimenta o mesmo `enqueue_transaction` do ingestor atual, com healthcheck e fallback para o ZMQ local. Sem tocar em `tx_to_word`, dedup, epoch, lease, Redis ou frontend.

---

## 7. Fontes

- mempool.space: [REST](https://mempool.space/docs/api/rest) · [WebSocket](https://mempool.space/docs/api/websocket) · [signet REST](https://mempool.space/signet/docs/api/rest) · [signet WS](https://mempool.space/signet/docs/api/websocket) · [Enterprise](https://mempool.space/enterprise) · [ToS](https://mempool.space/terms-of-service) · [FAQ](https://mempool.space/docs/faq) · [Discussion #752 (rate limits)](https://github.com/mempool/mempool/discussions/752) · [websocket-handler.ts (limites)](https://github.com/mempool/mempool/blob/master/backend/src/api/websocket-handler.ts)
- Blockstream: [docs](https://developer.blockstream.com/api/) · testes ao vivo (mainnet/signet/testnet `/mempool/recent` + `/tx/:txid`)
- Baseline do projeto: `docs/baseline-ingestao.md`
