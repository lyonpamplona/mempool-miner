# Auditoria Backend / WebSocket — Mempool Miner

> **Data:** 2026-08-19 · **Status:** Diagnóstico consolidado (sem correções aplicadas)
> **Escopo:** `backend/app/*.py`, `frontend/game.js`, suíte de testes, contratos WS/REST

---

## 1. Arquitetura

```
┌─────────────┐     HTTP/WS      ┌──────────────────┐     Redis PubSub     ┌──────────────┐
│   Browser    │ ◄──────────────► │   FastAPI (API)   │ ◄──────────────────► │  Ingestor(s)  │
│  game.js     │                  │   main.py         │                     │  ingestor.py  │
│  index.html  │                  │   ~4895 linhas    │                     │  (1/realm)    │
└─────────────┘                  └──────────────────┘                     └──────────────┘
                                      │                                      │
                                      │                                      │ ZMQ
                                      ▼                                      ▼
                                 ┌─────────────┐                      ┌──────────────┐
                                 │    Redis     │                      │ Bitcoin Core  │
                                 │  (asyncio)   │                      │  (RPC + ZMQ)  │
                                 └─────────────┘                      └──────────────┘
```

- **API (FastAPI)**: Processo stateless, escalável. Não abre ZMQ nem consulta RPC. Consome eventos namespaced do Redis.
- **Ingestor**: Singleton por realm. Conecta ZMQ ao Bitcoin Core, publica eventos no Redis com prefixo `mempool_miner:v2:{realm}`.
- **Redis**: PubSub para broadcast de eventos em tempo real + storage (leaderboard, player state, market, season).
- **WebSocket**: `/ws/v1/game/{realm_id}` — handshake com `game_start`, depois broadcast de eventos via Redis PubSub.
- **Multi-realm**: Cada rede (signet, testnet, mainnet) tem namespace isolado no Redis e ingestor independente.

### Módulos do Backend

| Arquivo | Responsabilidade |
|---------|-----------------|
| `main.py` | Rotas REST, WebSocket, middleware, endpoints de jogo (~4895 linhas) |
| `config.py` | Catálogo de redes, validação de realm_id, NodeConfig |
| `engine.py` | Motor de metadados, integração RPC, validação de transações |
| `blockchain.py` | Cliente ZMQ assíncrono (rawtx, hashblock) |
| `ingestor.py` | Ingestor singleton por realm (ZMQ → Redis) |
| `storage.py` | Chaves Redis isoladas por realm, migração de nomes legados |
| `events.py` | Contratos de eventos Bitcoin multi-rede |
| `global_events.py` | Scheduler de eventos globais (Fee Spike, Golden Rush, Mempool Flood) |
| `season_pass.py` | Season Pass — passaporte de temporada (272 linhas) |
| `ingestor_healthcheck.py` | Healthcheck baseado em heartbeat do Redis |

---

## 2. Contrato WebSocket

### Endpoint
- **URL:** `ws://host/ws/v1/game/{realm_id}`
- **Rota FastAPI:** `@app.websocket("/ws/v1/game/{realm_id}")` → `serve_websocket(websocket, realm_id)`
- **Alias legado:** `@app.websocket("/ws/game")` → `serve_websocket(websocket, DEFAULT_REALM_ID)` (linha 4593-4596)

### Handshake Confirmado
1. Cliente conecta com `Origin` válido
2. Backend aceita conexão e envia `game_start` como primeiro evento
3. Cliente processa `game_start` e inicia sessão
4. Eventos subsequentes chegam via Redis PubSub → `serve_websocket` → broadcast

### Evidência
- ✅ WebSocket signet aceita `Origin` e envia `game_start`
- ✅ Chamada direta `startSession` funciona
- ❌ **Dead code** em `main.py:4677`: `await serve_websocket(websocket, DEFAULT_REALM_ID)` dentro de um bloco `except` do endpoint `buy_season_premium` — código órfão que nunca executa

---

## 3. Mismatches REST — 25 Chamadas Frontend Sem Rota Correspondente

### Problema Crítico
O frontend usa URLs **curtas** (`/api/${activeRealmId}/...`) enquanto o backend expõe URLs **longas** (`/api/v1/networks/{realm_id}/...`).

| # | Frontend (game.js) | Backend (main.py) | Status |
|---|-------------------|-------------------|--------|
| 1 | `/api/${realm}/cards/{miner}` | `/api/v1/networks/{realm}/cards/{username}` | ❌ 404 |
| 2 | `/api/${realm}/crates/inventory/{miner}` | `/api/v1/networks/{realm}/crates/inventory/{username}` | ❌ 404 |
| 3 | `/api/${realm}/crates/open` | `/api/v1/networks/{realm}/crates/open` | ❌ 404 |
| 4 | `/api/${realm}/energy/buy/{miner}` | `/api/v1/networks/{realm}/energy/buy/{username}` | ❌ 404 |
| 5 | `/api/${realm}/energy/spend/{miner}` | `/api/v1/networks/{realm}/energy/spend/{username}` | ❌ 404 |
| 6 | `/api/${realm}/leaderboard` | `/api/v1/networks/{realm}/leaderboard` | ❌ 404 |
| 7 | `/api/${realm}/market/listings` | `/api/v1/networks/{realm}/market/listings` | ❌ 404 |
| 8 | `/api/${realm}/market/list` | `/api/v1/networks/{realm}/market/list` | ❌ 404 |
| 9 | `/api/${realm}/market/buy` | `/api/v1/networks/{realm}/market/buy` | ❌ 404 |
| 10 | `/api/${realm}/market/cancel` | `/api/v1/networks/{realm}/market/cancel` | ❌ 404 |
| 11 | `/api/${realm}/miner/register` | `/api/v1/networks/{realm}/miner/register` | ❌ 404 |
| 12 | `/api/${realm}/miner/status` | `/api/v1/networks/{realm}/miner/status` | ❌ 404 |
| 13 | `/api/${realm}/nodes` | `/api/v1/networks/{realm}/nodes` | ❌ 404 |
| 14 | `/api/${realm}/nodes/{id}/execute` | `/api/v1/networks/{realm}/nodes/{id}/execute` | ❌ 404 |
| 15 | `/api/${realm}/nodes/{id}/close` | `/api/v1/networks/{realm}/nodes/{id}/close` | ❌ 404 |
| 16 | `/api/${realm}/powerups` | `/api/v1/networks/{realm}/powerups` | ❌ 404 |
| 17 | `/api/${realm}/powerups/use` | `/api/v1/networks/{realm}/powerups/use` | ❌ 404 |
| 18 | `/api/${realm}/season` | `/api/v1/networks/{realm}/season` | ❌ 404 |
| 19 | `/api/${realm}/season/claim` | `/api/v1/networks/{realm}/season/claim` | ❌ 404 |
| 20 | `/api/${realm}/season/premium` | `/api/v1/networks/{realm}/season/premium` | ❌ 404 |
| 21 | `/api/${realm}/sprint` | `/api/v1/networks/{realm}/sprint` | ❌ 404 |
| 22 | `/api/${realm}/sprint/leaderboard` | `/api/v1/networks/{realm}/sprint/leaderboard` | ❌ 404 |
| 23 | `/api/${realm}/submit` | `/api/v1/networks/{realm}/submit` | ❌ 404 |
| 24 | `/api/${realm}/transactions` | `/api/v1/networks/{realm}/transactions` | ❌ 404 |
| 25 | `/api/${realm}/wallet` | `/api/v1/networks/{realm}/wallet` | ❌ 404 |

**Impacto:** Todas as 25 chamadas fetch() com template curto retornam **404 Not Found**. O jogo só funciona via WebSocket — nenhuma chamada REST direta do frontend atinge o backend.

**Nota:** Algumas chamadas usam URLs construídas dinamicamente (variáveis `url`, `NETWORKS_URL`) que podem gerar URLs longas corretas. As 25 acima são templates literais no código.

---

## 4. Erros 500 Reais (Runtime)

### 4.1 Season Pass — `coroutine` object has no attribute 'get'

**Arquivo:** `backend/app/season_pass.py`
**Linhas afetadas:** 110, 169, 181, 185, 200, 228

**Causa:** `season_pass.py` importa `redis.asyncio` mas **não usa `await`** nas chamadas Redis. Todas as funções (`get_season_data`, `add_season_xp`, `claim_season_reward`) são síncronas (`def`, não `async def`) mas recebem `redis_client` assíncrono.

```python
# Linha 110 — FALHA
raw = redis_client.hgetall(sk_key)  # ← retorna coroutine, não dict
current_level = int(raw.get("level", 0))  # ← TypeError: 'coroutine' object has no attribute 'get'

# Linha 169 — FALHA (mesmo padrão)
raw = redis_client.hgetall(sk_key)

# Linha 181-185 — FALHA (escrita sem await)
redis_client.hset(sk_key, mapping={...})
redis_client.expire(sk_key, 86400 * 30)

# Linha 200 — FALHA (claim_season_reward)
raw = redis_client.hgetall(sk_key)
```

**Severidade:** 🔴 **CRÍTICA**
**Impacto:** Endpoint `/api/v1/networks/{realm}/season` retorna **500 Internal Server Error** para qualquer jogador. Season Pass completamente inoperante.

### 4.2 Market — `zrange() got multiple values for argument 'start'`

**Arquivo:** `backend/app/main.py:2399`

```python
# Linha 2399 — FALHA
raw_listings = await redis_client.zrange(key, 0, -1, withscores=True, start=0, num=limit)
```

**Causa:** `redis.asyncio.zrange()` usa assinatura posicional `(key, start, end, ...)` mas a chamada passa `0, -1` como start/end **e também** `start=0` como keyword — conflito de argumento duplicado.

**Severidade:** 🔴 **CRÍTICA**
**Impacto:** Endpoint `/api/v1/networks/{realm}/market/listings` retorna **500 Internal Server Error**. Mercado completamente inoperante.

### 4.3 Dead Code — `serve_websocket` Órfã

**Arquivo:** `backend/app/main.py:4677`

```python
# Dentro do endpoint buy_season_premium, após o bloco try/except:
    except Exception as e:
        logger.error("Erro ao comprar premium: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    await serve_websocket(websocket, DEFAULT_REALM_ID)  # ← LINHA 4677: NUNCA EXECUTA
```

**Causa:** Código colado incorretamente dentro de uma função REST (`buy_season_premium`). A linha está após `raise HTTPException`, logo é inalcançável. Além disso, a função não tem parâmetro `websocket`.

**Severidade:** 🟡 **MODERADA** (dead code, não quebra nada)
**Impacto:** Poluição de código, risco de confusão em refatorações futuras.

### 4.4 Dead Code — WebSocket Legado

**Arquivo:** `backend/app/main.py:4593-4596`

```python
@app.websocket("/ws/game")
async def websocket_legacy(websocket: WebSocket) -> None:
    """Alias temporário restrito ao realm padrão."""
    await serve_websocket(websocket, DEFAULT_REALM_ID)
```

**Severidade:** 🟡 **MODERADA**
**Impacto:** Endpoint legado sem realm_id — força conexão ao realm padrão. Funcional mas viola o padrão multi-realm.

---

## 5. Suíte de Testes — Diagnóstico

**Comando:** `.venv/bin/pytest tests/ -q --tb=line`
**Resultado:** `11 failed, 67 passed, 6 errors` em 0.83s

### 5.1 Bugs Runtime (Falhas Reais) — 6 falhas

| Teste | Arquivo:Linha | Erro | Causa |
|-------|-------------|------|-------|
| `test_rpc_rejects_non_object_json` (3 parametrizações) | `test_engine.py` | `ValueError: NODE_ID regtest-test diverge do catálogo para regtest` | `config.py:157` — validação de NODE_ID mais estrita que o fixture do teste |
| `test_security_headers_cors_and_host_validation` | `test_models.py:100` | `assert 404 == 400` | Teste espera 400 mas rota retorna 404 (mismatch de URL) |
| `test_ws_sender_filters_each_redis_message` | `main.py:1869` | `AttributeError: 'str' object has no attribute 'queue'` | Bug no código: variável string usada onde se espera objeto com `.queue` |
| `test_submit_score_reports_an_existing_record_update` | `test_models.py:504` | `AssertionError: JSONResponse != dict` | Teste compara objeto Response com dict — assertion incorreta |

### 5.2 Testes Obsoletos (Fixture Removido) — 5 falhas

| Teste | Arquivo:Linha | Erro | Causa |
|-------|-------------|------|-------|
| `test_old_transaction_cannot_publish_after_new_block` | `test_multi_network.py:229` | `NameError: name 'create_mock_ingestor' is not defined` | Fixture `create_mock_ingestor` removido/renomeado |
| `test_stale_lease_cannot_commit_transaction` | `test_multi_network.py:285` | `NameError: name 'create_mock_ingestor' is not defined` | Mesmo problema |
| `test_status_keeps_runtime_token_out_of_public_event` | `test_multi_network.py:316` | `NameError: name 'create_mock_ingestor' is not defined` | Mesmo problema |
| `test_close_updates_status_and_releases_lease_atomically` | `test_multi_network.py:347` | `NameError: name 'create_mock_ingestor' is not defined` | Mesmo problema |
| `test_old_owner_does_not_remove_successor_token_file` | `test_multi_network.py:370` | `NameError: name 'create_mock_ingestor' is not defined` | Mesmo problema |

### 5.3 Erros de Setup (Fixture Quebrado) — 6 erros

| Teste | Arquivo | Erro | Causa |
|-------|---------|------|-------|
| `test_zmq_listener_starts_and_stops` | `test_blockchain.py` | `TypeError: NodeConfig.__init__() missing 2 required positional arguments: 'rpc_user' and 'rpc_password'` | `conftest.py` cria `NodeConfig` sem `rpc_user`/`rpc_password` |
| `test_zmq_source_uses_local_sequence` | `test_blockchain.py` | Mesmo erro | Mesmo problema |
| `test_zmq_source_ignores_third_frame` | `test_blockchain.py` | Mesmo erro | Mesmo problema |
| `test_zmq_listener_dispatches_rawtx` | `test_blockchain.py` | Mesmo erro | Mesmo problema |
| `test_zmq_listener_dispatches_hashblock` | `test_blockchain.py` | Mesmo erro | Mesmo problema |
| `test_zmq_listener_ignores_incomplete_message` | `test_blockchain.py` | Mesmo erro | Mesmo problema |

---

## 6. Resumo de Severidade

| ID | Problema | Arquivo:Linha | Severidade | Impacto |
|----|----------|-------------|-----------|---------|
| **P1** | 25 endpoints REST retornam 404 (mismatch URL) | `game.js` × `main.py` | 🔴 CRÍTICA | Jogo não funciona via REST; depende 100% de WebSocket |
| **P2** | Season Pass — Redis async sem await | `season_pass.py:110,169,181,185,200` | 🔴 CRÍTICA | Season Pass retorna 500; feature completamente quebrada |
| **P3** | Market — zrange argumento duplicado | `main.py:2399` | 🔴 CRÍTICA | Mercado retorna 500; feature completamente quebrada |
| **P4** | Dead code serve_websocket em endpoint REST | `main.py:4677` | 🟡 MODERADA | Código inalcançável; risco de confusão |
| **P5** | WebSocket legado sem realm_id | `main.py:4593-4596` | 🟡 MODERADA | Viola padrão multi-realm; funcional |
| **P6** | Teste ws_sender — str sem .queue | `main.py:1869` | 🟠 ALTA | Bug runtime em código de produção |
| **P7** | 5 testes obsoletos (fixture removido) | `test_multi_network.py` | 🟡 MODERADA | Ruído na suíte; não afeta produção |
| **P8** | 6 erros de setup (NodeConfig) | `test_blockchain.py` × `conftest.py` | 🟡 MODERADA | Testes de blockchain não rodam; não afeta produção |
| **P9** | 3 testes engine — NODE_ID diverge | `test_engine.py` × `config.py:157` | 🟡 MODERADA | Fixture desatualizado com validação de config |
| **P10** | Teste security_headers — assertion 404≠400 | `test_models.py:100` | 🟢 BAIXA | Teste incorreto; não indica bug em produção |
| **P11** | Teste submit_score — compara Response com dict | `test_models.py:504` | 🟢 BAIXA | Assertion de teste incorreta |

---

## 7. Recomendações (Priorizadas)

### Imediatas (bloqueiam funcionalidade)
1. **Corrigir season_pass.py**: Converter todas as funções para `async def` e adicionar `await` em todas as chamadas Redis (`hgetall`, `hset`, `expire`, `hincrby`).
2. **Corrigir main.py:2399**: Remover `start=0, num=limit` keyword args de `zrange()` — usar apenas assinatura posicional `zrange(key, 0, -1, withscores=True)` ou slice com `limit` aplicado após.
3. **Corrigir main.py:1869**: Investigar atribuição de string onde se espera objeto com `.queue`.

### Estruturais
4. **Alinhar URLs frontend/backend**: Ou o frontend usa URLs longas (`/api/v1/networks/{realm}/...`) ou o backend adiciona rotas curtas (`/api/{realm}/...`). Recomenda-se rotas curtas no backend como alias.
5. **Remover dead code**: `main.py:4677` (linha órfã) e avaliar se `main.py:4593-4596` (alias legado) deve ser removido.

### Suíte de Testes
6. **Atualizar conftest.py**: Adicionar `rpc_user` e `rpc_password` ao fixture `NodeConfig` para os 6 erros de `test_blockchain.py`.
7. **Remover/reatualizar 5 testes obsoletos** em `test_multi_network.py` que referenciam `create_mock_ingestor`.
8. **Corrigir assertions** em `test_models.py:100` e `test_models.py:504`.

---

## 8. Evidências Coletadas

- **Transcript:** `/home/developer/.hermes/cache/delegation/live/deleg_0fe82aa5/task-1.log`
- **Testes:** `.venv/bin/pytest tests/ -q --tb=line` → 11 failed, 67 passed, 6 errors
- **WebSocket:** Conectado manualmente em signet — `game_start` recebido ✅
- **startSession:** Chamada direta funciona ✅
- **Fontes verificadas:** `main.py` (4895 linhas), `season_pass.py` (272 linhas), `game.js`, `config.py`, `conftest.py`

---

*Relatório gerado automaticamente — auditoria estática + execução de testes. Sem correções aplicadas.*
