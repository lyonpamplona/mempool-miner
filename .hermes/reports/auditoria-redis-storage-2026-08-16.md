# Auditoria Redis/Storage — Mecânicas de Jogo

**Data:** 2026-08-16  
**Arquivos auditados:** `storage.py`, `ingestor.py`, `engine.py`, `main.py`, `config.py`, `events.py`  
**Diretórios verificados:** `models/` (não existe), `services/` (não existe)

---

## 1. Motor de Consenso

### 1.1 Proof-of-Search — barra de progresso global
- **Status:** ❌ NÃO IMPLEMENTADA no Redis/Storage
- **Detalhe:** O campo `verification_progress` presente no snapshot (`realm_state_key`) é apenas um repasse do `getblockchaininfo` do Bitcoin Core — representa o progresso de IBD do nó, não uma barra de progresso de jogo. Não há nenhum contador, sorted set ou campo dedicado ao progresso do jogador.
- **Chaves Redis relevantes:** `mempool_miner:v2:{realm}:state` — contém apenas dados operacionais do nó.

### 1.2 Halving Protocol — contador de blocos, redução de tempo
- **Status:** ❌ NÃO IMPLEMENTADA no Redis/Storage
- **Detalhe:** Existe um contador de blocos (`epoch_block_counter_key`) que incrementa a cada bloco e reseta a cada 2016 blocos, mas ele serve exclusivamente para o reset do leaderboard (epochs), não para halving. Não há nenhum mecanismo de redução de recompensa, multiplicador de dificuldade ou controle de tempo baseado em halving.
- **Chaves Redis relevantes:** `mempool_miner:v2:{realm}:block_counter`, `mempool_miner:v2:{realm}:epoch_id` — usadas apenas para epoch do leaderboard.

---

## 2. Eventos On-Chain

### 2.1 STD / HIGH FEE / GOLDEN HASH — metadados das transações
- **Status:** ✅ IMPLEMENTADA
- **Onde:** `engine.py` → `get_tx_metadata()` (linhas 136-186)
- **Como funciona:**
  - `is_golden`: Verifica se o txid começa com `"00"` (1/256 de chance)
  - `is_high_fee`: Verifica se `fee_rate_sat_vb >= config.high_fee_rate_sat_vb` (default 20 sat/vB)
  - `word`: Deriva palavra BIP39 dos primeiros 128 bits do txid
  - `vsize` e `fee_rate_sat_vb`: Obtidos via RPC `getmempoolentry`
- **Armazenamento:** Os metadados são embutidos no evento `transaction_received` publicado via PubSub no canal `mempool_miner:v2:{realm}:events`. Não há persistência individual de transações — apenas dedupe via `SADD` no set `mempool_miner:v2:{realm}:seen:{epoch}` com TTL de 3600s.
- **Contador:** `mempool_miner:v2:{realm}:mempool_count` — inteiro incrementado via `INCR` no script `COMMIT_TRANSACTION_SCRIPT`.

### 2.2 MEV Oculto — flag `is_mev` nas transações
- **Status:** ✅ IMPLEMENTADA
- **Onde:** `engine.py` → `get_tx_metadata()` (linha 185), `ingestor.py` → `process_transaction()` (linha 427)
- **Como funciona:** `is_mev = int(txid[:8], 16) % 100 < 10` — ~10% de chance determinística baseada no txid. A flag é incluída no evento e exposta no contrato público (`PUBLIC_EVENT_FIELDS["transaction_received"]` em `main.py` linha 83).

### 2.3 Slashing — saldo Cold Wallet, contador de erros
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum campo, contador ou estrutura Redis relacionada a slashing, cold wallet, saldo penalizável ou contador de erros. A única menção a "slashing" encontrada está em documentos (README, docs, relatórios) e no frontend (`game.js`), mas não há backing no backend/Redis.

### 2.4 Combo Hashrate — multiplicador por jogador
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum multiplicador de hashrate, combo system ou tracking de combos no Redis/Storage. O leaderboard é um sorted set simples (`ZADD`) sem qualquer lógica de multiplicação ou combo.

---

## 3. Economia Interna

### 3.1 Reveal Hint — custo 5.000 SATS, hint-glow
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum campo de custo de hint, saldo de satoshis do jogador, hint-glow ou sistema de revelação no Redis/Storage.

### 3.2 Hardware Upgrades — nível do jogador (CPU/GPU/ASIC/Quantum)
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum sistema de níveis, inventário de hardware ou progresso de upgrades no Redis/Storage. As palavras "cpu", "gpu", "asic", "quantum" aparecem apenas no frontend (`game.js`, `index.html`, `style.css`) e em documentos — sem backing no backend.

### 3.3 Lightning Channel L2 — canal ativo, timer 5 blocos
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum canal Lightning, timer de 5 blocos ou mecanismo L2 no Redis/Storage. A palavra "lightning" aparece apenas em documentos e no frontend.

### 3.4 Orphan Block RBF — botão emergência, timer 15s
- **Status:** ❌ NÃO IMPLEMENTADA
- **Detalhe:** Não existe nenhum botão de emergência, timer de 15 segundos ou mecanismo RBF de bloco órfão no Redis/Storage.

---

## 4. Ecossistema Social

### 4.1 Mining Pools — tag [TAG] no login, soma de satoshis
- **Status:** ✅ IMPLEMENTADA
- **Onde:** `main.py` → `submit_score_for_realm()` (linhas 501-545), `_extract_pool_prefix()` (linhas 548-562)
- **Como funciona:**
  - Se o username começa com `[` e contém `]`, extrai o nome da pool: `username[1:username.index("]")]`
  - Exemplo: `[BraiNspiral] MinerX` → pool name = `BraiNspiral`
  - Atualiza simultaneamente o leaderboard individual (`leaderboard_key`) e o leaderboard de pools (`pool_leaderboard_key`)
  - Endpoint dedicado: `GET /api/v1/networks/{realm_id}/pools` retorna top 10 pools
- **Chave Redis:** `mempool_miner:v2:{realm}:pools` — sorted set com pool_name → score.

### 4.2 Leaderboard Epochs — reset a cada 2016 blocos
- **Status:** ✅ IMPLEMENTADA
- **Onde:** `ingestor.py` → `_increment_block_counter()` (linhas 537-585)
- **Como funciona:**
  - Script Lua atômico (`RESET_SCRIPT`) executado a cada bloco via `handle_block()`
  - Incrementa `block_counter` (chave `epoch_block_counter_key`)
  - Se `count >= 2016`: deleta o leaderboard antigo (`DEL`), incrementa `epoch_id`, zera o contador
  - Publica evento `leaderboard_reset` no canal de eventos via PubSub
  - O evento é sanitizado e entregue via WebSocket ao cliente
- **Chaves Redis:**
  - `mempool_miner:v2:{realm}:block_counter` — inteiro, reseta a cada 2016
  - `mempool_miner:v2:{realm}:epoch_id` — inteiro, incrementa a cada reset
  - `mempool_miner:v2:{realm}:leaderboard` — sorted set, deletado e recriado a cada epoch

---

## Resumo Executivo

| # | Mecânica | Status | Chaves Redis |
|---|----------|--------|--------------|
| 1.1 | Proof-of-Search (progresso) | ❌ Não implementada | — |
| 1.2 | Halving Protocol | ❌ Não implementada | — |
| 2.1 | STD/HIGH FEE/GOLDEN HASH | ✅ Implementada | `mempool_count`, `seen:{epoch}`, `events` |
| 2.2 | MEV Oculto | ✅ Implementada | `events` (campo `is_mev`) |
| 2.3 | Slashing | ❌ Não implementada | — |
| 2.4 | Combo Hashrate | ❌ Não implementada | — |
| 3.1 | Reveal Hint | ❌ Não implementada | — |
| 3.2 | Hardware Upgrades | ❌ Não implementada | — |
| 3.3 | Lightning Channel L2 | ❌ Não implementada | — |
| 3.4 | Orphan Block RBF | ❌ Não implementada | — |
| 4.1 | Mining Pools | ✅ Implementada | `pools` (sorted set) |
| 4.2 | Leaderboard Epochs | ✅ Implementada | `block_counter`, `epoch_id`, `leaderboard` |

**Total:** 4 de 12 mecânicas implementadas no Redis/Storage (33%)

**Observações:**
- Os diretórios `models/` e `services/` não existem — não há camadas adicionais de abstração de dados.
- As mecânicas implementadas são focadas em eventos on-chain (metadados de TX, MEV) e ecossistema social (pools, leaderboard com epochs).
- As 8 mecânicas não implementadas cobrem economia interna (hints, upgrades, lightning, RBF), consenso (progresso, halving) e eventos on-chain avançados (slashing, combo).
- O frontend (`game.js`, `index.html`) contém referências visuais a mecânicas não implementadas — há uma desconexão entre a interface e o backend.
