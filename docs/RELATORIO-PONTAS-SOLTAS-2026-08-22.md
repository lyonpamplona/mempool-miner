# Relatório — Pontas Soltas do Mempool Miner (Teste Real)

**Data:** 2026-08-22
**Método:** 4 subagentes em paralelo (somente leitura) + validação ao vivo (Redis, logs, RPC, WebSocket)
**Escopo:** Sintomas reportados pelo usuário após teste real do jogo

---

## Status das Correções (aplicado em 2026-08-22)

| # | Sintoma | Fase | Correção aplicada | Validação |
|---|---------|------|-------------------|-----------|
| 1 | Feed esgota | 1 | Faucet contínuo no `entrypoint.sh` (12 TXs/20s + bloco/60s) + remoção de `-prune=550` | regtest `playable:true`, IBD resolvido, mempool reposta |
| 2 | Saldo insuficiente | 2 | Causa raiz: `hset` com bool Python → `DataError` (sync **sempre** falhava). Coerção para string + `persist(key)` + reconciliação no load (máximo local×backend) + retry no sync | POST player-state 200, balance gravado, TTL -1, compra de energia OK |
| 3 | PROGRESSÃO 500 | 4 | `Math.round` no XP (frontend) + `int(float(...))` no backend + migração `67.5→67` | GET season 200, add-xp com float coerção OK |
| 4 | Aguardando sessão | 5 | Retry (3×) nos inicializadores + handler `pageshow` (bfcache) + `TAB_INITIALIZERS` + re-chamada no `showTab` | código servido (v38) |
| 5 | Sessão expirada | 6 | Flag `roundSettled` — tick do timer não sobrescreve o sucesso | código servido (v39) |
| 6 | Tempo acelera | 7 | Timer por timestamp (`raceEndTime`, tick 250ms, imune a throttling) + limite efetivo no HUD (`LIMIT XXs`) | código servido (v40) |
| 7 | Bloco duplicado | 3 | `COMMIT_BLOCK_SCRIPT` só publica em mudança real de epoch + dedup frontend por `block_hash`/`epoch` + flag `orphanOfferedThisRound` | teste Redis: 3 chamadas → 2 mensagens (dedup OK) |
| 8 | Mercado inerte | 8 | CTA nos estados vazios (COMPRAR: "venda o seu"; VENDER: "jogue para ganhar") | código servido (v41) |

**CACHE_VERSION:** v34 → v42 (bump a cada fase que alterou o shell).
**Suíte:** 166 passed após cada fase.

## Auditoria Final (4 subagentes independentes) + Correções

4 subagentes em paralelo (backend, frontend, funcional ao vivo, qualidade/código morto) confirmaram as correções e apontaram pontas soltas. Todas as de severidade **ALTO** e os itens **MÉDIO/BAIXO** seguros foram corrigidos e validados (v42):

| # | Severidade | Achado da auditoria | Correção |
|---|-----------|---------------------|----------|
| A1 | **ALTO** | `main.py:1488` — 8º `expire(state_key, 86400)` não removido (TTL 24h no player state após claim de missão) | `expire` → `persist(state_key)` |
| A2 | **ALTO** | `game.js:5072` — `querySelector('.decoder-content')` lançava **TypeError em todo acerto do decoder** (classe não existe), interrompendo saldo+5.000/streak/sync | Guard `if (decoderContent)` |
| A3 | **ALTO** | `missions` mapeado para `perfil` no `TAB_INITIALIZERS`, mas o painel está na tab `competir` — ficava "Aguardando sessão." para sempre após teardown | `competir: ['missions']` |
| A4 | **ALTO** | CTA de venda (`market-sell-empty`) dentro de `#market-sell` com `display:none` permanente — nunca visível | Toggle: VENDER abre a seção (`.market-sell-open`) / já aberta executa a venda |
| A5 | MÉDIO | Focus-trap de Tab consultava `.modal-overlay.active`; modais reais usam `.modal-wrap` → trapa desativada (a11y) | `.modal-wrap.active` |
| A6 | MÉDIO | 4 blocos de listeners órfãos (`.market-tab-btn`, `.card-filter`, `.season-tab`, `.staking-duration-btn`) — classes não existem no HTML | Removidos |
| A7 | BAIXO | `season_pass.py:188` — `int(xp_amount)` quebraria com string decimal `"67.5"` | `int(float(xp_amount))` |
| A8 | BAIXO | `currentSeasonTab` write-only (só usado no listener morto) | Removida |

**Validação pós-auditoria (v42):** suíte 166 passed · POST player-state 200 · balance 10720 no Redis · **TTL -1 (persistente)** · 4 correções ALTO presentes no `game.js` servido · 0 referências ao código morto removido · `#market-sell.market-sell-open` no CSS servido.

**Pontas soltas restantes (documentadas, não bloqueantes):**
- Reconciliação max-based pode ressuscitar sats gastos se o backend estiver stale-alto (jogo simulado, severidade baixa).
- Dedup de `block_mined` guarda só o último hash/epoch (re-entrega de bloco anterior seria re-processada; risco baixo).
- `hardware_level`/`lightning_active` só são espelhados backend→local (nunca local→backend quando local > backend).
- Variáveis top-level nunca usadas: `marketSellEl` (agora usada no toggle), `cardsPanelEl`, `chatPanelEl`, `friendsPanelEl`, `missionsPanelEl`, `seasonPanelEl`, `skillsHeaderEl`, `skillsPanelEl`.
- CSS órfão espelhando o JS morto removido (`.market-tab-btn`, `.season-tab`, `.card-filter`, `.staking-duration-btn`, `.decoder-content`, `.modal-overlay`).
- Comentários "Fase N" com fase errada/contraditória entre JS e HTML (rotulagem, não comportamento).
- `FAUCET_*`/`BLOCK_INTERVAL` ausentes de `.env.example` (documentação).

---

## Resumo Executivo

| # | Sintoma | Severidade | Causa raiz (arquivo:linha) | Status |
|---|---------|-----------|------------------------------|--------|
| 1 | Feed esgota após ~3 rodadas | **CRÍTICO** | regtest em IBD (`playable:false`) + sem fonte contínua de TXs | Confirmado ao vivo |
| 2 | "Saldo insuficiente" com 10.720 sats | **CRÍTICO** | Divergência localStorage (10.720) × Redis (147 sats) | Confirmado ao vivo |
| 3 | PROGRESSÃO erro ao carregar | **ALTO** | XP float no Redis → `int("67.5")` → 500 | Confirmado nos logs |
| 4 | "Aguardando sessão" em todas as abas | **ALTO** | Loaders one-shot + sem `pageshow`/retry | Confirmado no código |
| 5 | "Sessão expirada" ao achar todas as palavras | **ALTO** | Corrida timer × `showResult` (janela 600ms) | Confirmado no código |
| 6 | Tempo "acelera" em algumas rodadas | **MÉDIO** | `networkTimeLimit` menor (Lightning/RBF/Halving) | Confirmado no código |
| 7 | "Bloco mineirado" duplicado | **CRÍTICO** | Handler sem dedup + backend re-publica | Confirmado no código |
| 8 | Mercado sem preços / comprar-vender inertes | **ALTO** | Mercado vazio (consequência do feed) | Confirmado ao vivo |

---

## Detalhamento por Sintoma

### 1. Feed esgota após ~3 rodadas — CRÍTICO

**Evidência ao vivo:**
- Redis `mempool_miner:v2:{regtest}:state`: `"status":"syncing","playable":false,"initial_blockdownload":true,"verification_progress":0.483,"pruned":true`
- Log do nó regtest: `Potential stale tip detected` a cada 10 min há **horas** (última atualização: 28350s ≈ 7.9h)
- RPC do regtest em **timeout** (nó travado)
- `mempool_count` regtest = 36 TXs → 36/6 = **6 rodadas no máximo** (mas o IBD impede novas)
- signet: `"status":"ready","playable":true,"mempool_count":204` — funciona

**Causa raiz (2 camadas):**
1. **regtest preso em IBD** (`ingestor.py:355` → `self.playable = not in_ibd`; `ingestor.py:441` → descarta TX se `not self.playable`). O nó está com `verification_progress: 0.483` e `pruned: true` (prune=550) — regtest não deveria ter pruning.
2. **Sem fonte contínua de transações**: `bitcoin/entrypoint.sh:68-70` envia **apenas 10 TXs** no boot. Não há faucet/gerador que reponha a mempool. Mesmo com `playable=true`, o feed esgota.

**Por que o usuário vê "esperando transações":** o realm default é `regtest` (`config.py`), que está `playable:false` → o ingestor não publica nada → `txBuffer` nunca enche → "Aguardando transações (0/6)..." para sempre.

---

### 2. "Saldo insuficiente" com 10.720 sats — CRÍTICO

**Evidência ao vivo:**
- Redis `mempool_miner:v2:{signet}:player:developer` → `balance = 147` (sats)
- Redis `mempool_miner:v2:{regtest}:player:developer` → **inexistente** (TTL -2)
- UI mostra **10.720** (localStorage `balanceSatoshis`, `game.js:308/1286`)

**Causa raiz: duas fontes de verdade que divergem.**

| Papel | Onde | Valor |
|---|---|---|
| **Exibido** (o que o usuário vê) | `game.js:308` `balanceSatoshis` (localStorage) | 10.720 |
| **Validado** (o que o backend cobra) | Redis `player:{realm}:player:{user}.balance` | 147 (signet) / 0 (regtest) |

- O endpoint de compra `POST /energy/buy` (`main.py:4548`) executa `ENERGY_BUY_SCRIPT` (`storage.py:103-104`), que lê o saldo de **Redis**: `balance = tonumber(redis.call('hget', state_key, 'balance') or '0')` → `if balance < cost then return {-1, 0, balance} end`.
- Com `balance = 147` (signet) ou `0` (regtest) → `147 < 2000` → "Saldo insuficiente. Necessario 2000 sats" (`main.py:4582`).
- **Não é divergência de unidade** (ambos em sats: `ENERGY_BUY_COST = 2000`, `main.py:4410`) — é **chave Redis diferente/expirada** da que a UI exibe.

**Por que divergem (3 mecanismos):**
1. **Sync fire-and-forget falha em silêncio**: `syncPlayerState()` (`game.js:1887-1912`) faz `POST player/{username}` com o saldo local, mas é chamado com `void` (`game.js:2759,1987,2006,2025,2958,3881,4905`) e o `catch` só faz `console.warn` (`game.js:1908`). Se o POST falhar, o backend nunca recebe os 10.720.
2. **TTL do Redis expira o saldo**: `update_player_state` seta `expire(key, 86400)` (`main.py:935`). Se o estado expirou (24h), o backend volta a 0, mas o localStorage mantém 10.720.
3. **`loadPlayerState` não corrige a divergência**: `game.js:1925`: `if (state.balance > 0) balanceSatoshis = state.balance;` — se o backend está 0, o local **mantém** o valor alto. Nunca reconcilia para baixo.

**Impacto em cascata:** o mesmo bug afeta:
- `energy_recharge` (2.000 sats) → "saldo insuficiente"
- Crate 5K (`main.py:3782/3791`) → "Saldo insuficiente. Precisa de 5.000 sats"
- Compra no mercado (`main.py:2789-2792`) → "Saldo insuficiente. Custo total: … sats"
- Crate FREE (`main.py:3785-3786`) → "Nenhuma crate grátis disponível" (mensagem diferente, mas o usuário agrupou). **Confirmado:** o listener do botão FREE está correto (`game.js:7064` → `openCrate(true)` → `use_free: true`); o caminho FREE no backend não checa saldo, só `free_crates` (que é 0) — a mensagem real é "Nenhuma crate grátis disponível".

---

### 3. PROGRESSÃO erro ao carregar — ALTO

**Evidência nos logs:**
```
ERROR app.main: Erro ao obter dados da temporada: invalid literal for int() with base 10: '67.5'
GET /api/v1/networks/signet/season/developer HTTP/1.1 500 Internal Server Error
```

**Causa raiz (bidirecional):**
1. **Frontend envia XP float**: `calculateWordXP` (`game.js:7231-7235`) retorna `baseXP + comboBonus`, onde `comboBonus = comboMultiplier * 5`. O `comboMultiplier` aumenta em **0.5** (`game.js:2666`: `comboMultiplier = Math.min(comboMultiplier + 0.5, comboCap)`). Com `comboMultiplier = 1.5` → `comboBonus = 7.5` → `wordXP = 60 + 7.5 = 67.5` (float).
2. **Backend grava float no Redis**: `add_season_xp` (`season_pass.py:201-203`) faz `hset(sk_key, mapping={"xp": str(new_xp)})` → grava `"67.5"` (string de float).
3. **Backend lê com `int()`**: `get_season_data` (`season_pass.py:120`) faz `current_xp = int(raw.get("xp", 0))` → `int("67.5")` → **ValueError** → 500.

**Correção:** `Math.round` no frontend (`calculateWordXP`) + coerção `int()` no backend (`add_season_xp` e `get_season_data`).

---

### 4. "Aguardando sessão" em todas as abas — ALTO

**Causa raiz:**
- O placeholder "Aguardando sessão." é gravado por `resetSessionPanel` (`game.js:832-838`) dentro de `resetSessionModules` (`game.js:934-944`, 11 painéis).
- Esses painéis só são repopulados por `runSessionInitializers` (`game.js:535-543`) — **uma única vez** no fim de `startSession`.
- `showTab` (`game.js:68-85`) apenas alterna CSS (`tab.hidden`/`.active`) e **nunca re-dispara os loaders**.
- `teardownSession` é chamado em `pagehide` (`game.js:1272-1275`), em todo `socket.onclose` (`game.js:1423`), em troca de rede (`game.js:1253, 1377`) e em `network-not-playable`/`network-unavailable` (`game.js:1496, 1529`). Cada um deles zera os 11 painéis.
- **Não existe handler `pageshow`/bfcache**. Ao voltar via back/forward, `pagehide` já resetou os painéis e nada os repõe.
- Inicializadores que falham (404/rede/backend não pronto) não têm retry → painel fica no placeholder para sempre.

---

### 5. "Sessão expirada" ao encontrar todas as palavras — ALTO

**Causa raiz (corrida timer × "todas as palavras"):**
- O timer (`startNetworkRace`, `game.js:2857-2888`) e o handler de "todas as palavras" (`endSelection`, `game.js:2761-2780`) **não são atômicos**.
- Ao achar a última palavra, `endSelection` faz `clearInterval(networkInterval)` (`game.js:2762`) e `isPlaying=false` (`game.js:2763`), mas **adiada `showResult(true, …)` em 600 ms** via `scheduleForSession` (`game.js:2773-2778`).
- Essa janela de 600 ms é a vulnerabilidade: se o tick do `setInterval` já foi enfileirado no mesmo lote do event loop (ou `networkTimePassed >= networkTimeLimit` se completou no tick imediatamente anterior), `showResult(false, "O cronômetro da rodada expirou.")` (`game.js:2885`) dispara e **sobrescreve o sucesso**.

**Nota:** a string exata "Sessao expirada" só existe no backend do mini-game Decoder (`main.py:4790`). No jogo principal, a mensagem real é "O cronômetro da rodada expirou." (`game.js:2885`).

---

### 6. Tempo "acelera" em algumas rodadas — MÉDIO

**Causa raiz:**
- O timer **não acumula** (há `clearInterval` no início de `startNetworkRace` e em `prepareNextBlock`) e **não usa delta** — é um contador fixo `networkTimePassed++` a cada 1000 ms.
- A "aceleração" percebida vem de **`networkTimeLimit` menor**:
  - Lightning/L2: `networkTimeLimit = 20` (`game.js:2174, 2192`)
  - RBF: `networkTimeLimit = 15 + getNetworkTimeBonus()` (`game.js:2963`)
  - Halving: `networkTimeLimit -= halvingPenalty` (até −30 s) a cada rodada (`game.js:2201-2203`)
- Quando um `block_mined` duplicado reinicia a rodada (ver Sintoma 7), `prepareNextBlock` zera `networkTimePassed=0` e uma nova contagem — possivelmente mais curta — começa, o que **parece** aceleração.

---

### 7. "Bloco mineirado" duplicado — CRÍTICO

**Causa raiz (handler não idempotente + backend pode publicar 2×):**
1. **Backend sem guarda de mudança de epoch**: `handle_block` (`ingestor.py:541-590`) publica `block_mined` via `COMMIT_BLOCK_SCRIPT` (`ingestor.py:82-90`). O script só valida o token de lease e **não verifica se a epoch já é igual ao novo `block_hash`** — uma segunda entrega do mesmo bloco (re-entrega ZMQ) **re-publica** `block_mined`.
2. **Handler frontend sem dedup**: o handler `block_mined` (`game.js:1578-1622`) processa **todo** evento, sem deduplicar por `block_hash`/`epoch`.
3. **Janela do RBF reabre `isPlaying`**: no primeiro `block_mined` com `isPlaying=true`, chama-se `showOrphanBlockSalvage` (`game.js:1604 → 2924`). Se o usuário clica "Resgatar", `isPlaying=true` é re-setado (`game.js:2961`) e `startNetworkRace` reinicia (`game.js:2968`). Um **segundo** `block_mined` nessa janela volta a entrar no ramo `isPlaying` → `showOrphanBlockSalvage` de novo → **"Bloco minerado!" duplicado**.

**Sequência observada:** `block_mined`#1 → `prepareNextBlock` → `buildPlayableBlock` (palavras aparecem) → `startNetworkRace` com limite menor (acelerado) → `block_mined`#2 (duplicado) → `showOrphanBlockSalvage` → "Bloco minerado!" de novo.

---

### 8. Mercado sem preços / comprar-vender inertes — ALTO

**Evidência ao vivo:**
- `GET /market/list` regtest → `{"listings":[],"total":0}`
- `GET /market/list` signet → `{"listings":[],"total":0}`
- Redis `market:list` = `none` (chave inexistente) nos dois realms

**Causa raiz:**
- O mercado está **vazio** (nenhum listing). É um mercado P2P: só tem listings quando jogadores vendem power-ups. Ninguém vendeu → vazio.
- **Não há bug de rota nem de campo**: o backend **retorna** `price` (`main.py:2543`) e o frontend **o renderiza** (`game.js:6104`: `listing.price.toLocaleString()`).
- **Comprar não faz nada** porque não há listing para comprar.
- **Vender não faz nada** porque exige selecionar um power-up + preço; clicar em VENDER sem isso só dispara validação (`Selecione um power-up` / `Preço inválido`), parecendo "inerte".
- **Por que "itens só com nomes, sem preço"?** O que o usuário vê é a **aba VENDER** (dropdown com o inventário do jogador — nomes + contagem, sem preço, pois é inventário próprio) ou o **dropdown de filtro**. A aba COMPRAR, com o mercado vazio, mostra apenas o estado vazio.
- **Ligado ao Sintoma 1**: em regtest (IBD, não jogável) o jogador não minera/ganha power-ups → não tem o que vender → mercado vazio.

---

## Plano de Correção (Fases Priorizadas)

### Fase 1 — CRÍTICO: Feed de transações (Sintoma 1)
**Objetivo:** regtest jogável + fonte contínua de TXs

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 1.1 | Remover `-prune=550` do `bitcoin-regtest` (regtest não precisa de pruning) | `docker-compose.yaml` | Baixo |
| 1.2 | Reiniciar o nó regtest para limpar o estado de IBD | `docker compose restart bitcoin-regtest` | Baixo |
| 1.3 | Adicionar faucet/gerador de transações em regtest (loop em background no `entrypoint.sh` que envia N TXs a cada M segundos) | `bitcoin/entrypoint.sh` | Médio |
| 1.4 | Adicionar healthcheck que alerta quando `playable=false` | `docker-compose.yaml` | Baixo |

**Validação:** `getblockchaininfo` → `initialblockdownload: false`; `mempool_count` > 0 e crescente; `playable: true` no Redis.

### Fase 2 — CRÍTICO: Divergência de saldo (Sintoma 2)
**Objetivo:** saldo local e backend reconciliados

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 2.1 | Em `loadPlayerState`, **sempre** espelhar o backend: `balanceSatoshis = state.balance` (remover o `if > 0`) | `game.js:1925` | Baixo |
| 2.2 | No início de sessão, se `balanceSatoshis > 0` e o backend retornou `0`, chamar `syncPlayerState()` para empurrar o valor local | `game.js` (session init) | Médio |
| 2.3 | Tornar `syncPlayerState` confiável: retry com backoff (não só `console.warn`) | `game.js:1887-1912` | Médio |
| 2.4 | Remover o TTL de 24h do `player_state_key` (tornar persistente) | `main.py:935` | Baixo |

**Validação:** comprar energia/crate com saldo local > custo → sucesso; saldo no Redis = saldo na UI.

### Fase 3 — CRÍTICO: Bloco mineirado duplicado (Sintoma 7)
**Objetivo:** handler idempotente + backend não re-publica

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 3.1 | No handler `block_mined`, guardar `lastMinedBlockHash`/`lastMinedEpoch` e **ignorar** eventos com o mesmo `block_hash`/`epoch` | `game.js:1578-1622` | Médio |
| 3.2 | Tratar `showOrphanBlockSalvage` como "uma vez por rodada" (flag `orphanOfferedThisRound`) | `game.js:2924` | Baixo |
| 3.3 | Em `COMMIT_BLOCK_SCRIPT`, publicar `block_mined` **apenas se** `get(epoch_key) ~= ARGV[2]` (mudança real de epoch) | `ingestor.py:82-90` | Médio |

**Validação:** simular 2× `block_mined` com o mesmo hash → UI mostra "Bloco minerado!" apenas 1×.

### Fase 4 — ALTO: Progressão 500 (Sintoma 3)
**Objetivo:** XP sempre inteiro

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 4.1 | `calculateWordXP`: `return Math.round(baseXP + comboBonus)` | `game.js:7234` | Baixo |
| 4.2 | `add_season_xp`: coerção `xp_amount = int(xp_amount)` no início | `season_pass.py:183` | Baixo |
| 4.3 | `get_season_data`: `current_xp = int(float(raw.get("xp", 0)))` (tolerante a float legado) | `season_pass.py:120` | Baixo |
| 4.4 | Migrar dados existentes: `HSET season:developer xp "67"` (ou `int(float(...))` em batch) | Redis (script) | Baixo |

**Validação:** `GET /season/developer` → 200; `xp` no Redis é inteiro.

### Fase 5 — ALTO: "Aguardando sessão" em todas as abas (Sintoma 4)
**Objetivo:** painéis repopulados ao trocar de aba / voltar de bfcache

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 5.1 | Adicionar `window.addEventListener('pageshow', …)` que re-dispara `runSessionInitializers` quando `event.persisted` | `game.js` | Médio |
| 5.2 | Em `showTab`, se `sessionReady` e o loader daquele painel ainda não completou, re-chamar o loader correspondente | `game.js:68-85` | Médio |
| 5.3 | Dar retry com backoff nos inicializadores (máx. 3 tentativas) | `game.js:535-543` | Médio |

**Validação:** trocar de aba → painel repopulado; back/forward → painéis repopulados.

### Fase 6 — ALTO: "Sessão expirada" ao achar todas as palavras (Sintoma 5)
**Objetivo:** sucesso não é sobrescrito pelo timer

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 6.1 | Em `endSelection`, ao detectar `wordsFoundInBlock === blockWords.length`, chamar `showResult(true, …)` **sincronamente** (remover o `scheduleForSession` de 600 ms) | `game.js:2773-2778` | Baixo |
| 6.2 | Introduzir flag `roundSettled` que o tick do timer verifica antes de declarar expiração | `game.js:2883` | Baixo |

**Validação:** achar todas as palavras no último tick → "Rodada completa!" (não "expirou").

### Fase 7 — MÉDIO: Tempo "acelera" (Sintoma 6)
**Objetivo:** transparência + timer imune a throttling

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 7.1 | Exibir o `networkTimeLimit` efetivo no HUD (transparência) | `game.js` (HUD) | Baixo |
| 7.2 | Usar timer baseado em timestamp (`endTime = Date.now() + limit*1000`) em vez de contador por tick | `game.js:2857-2888` | Médio |

**Validação:** aba em segundo plano → timer não acelera; HUD mostra o limite efetivo.

### Fase 8 — ALTO: Mercado UX (Sintoma 8)
**Objetivo:** estado vazio claro + CTA

| # | Ação | Arquivo | Esforço |
|---|------|---------|---------|
| 8.1 | Na aba COMPRAR, quando `total===0`, exibir CTA claro ("Nenhum item à venda — venda o seu na aba VENDER") | `game.js:6074` | Baixo |
| 8.2 | Na aba VENDER, quando inventário vazio, exibir CTA ("Você não tem power-ups para vender — jogue para ganhar") | `game.js:6154` | Baixo |

**Validação:** mercado vazio → CTA claro (não "botão morto").

---

## Ordem de Execução Recomendada

1. **Fase 1** (feed) — sem isso, o jogo não funciona em regtest
2. **Fase 2** (saldo) — sem isso, nenhuma compra funciona
3. **Fase 3** (bloco duplicado) — quebra o loop principal
4. **Fase 4** (progressão 500) — bug concreto, fix rápido
5. **Fase 5** (aguardando sessão) — UX
6. **Fase 6** (sessão expirada) — UX
7. **Fase 7** (tempo acelera) — UX
8. **Fase 8** (mercado UX) — UX

**Estimativa total:** ~2-3 dias de trabalho (fases 1-3: ~1 dia; fases 4-8: ~1 dia).

---

## Observações

- **Nenhum arquivo foi editado** — este é um relatório de análise + plano.
- As 3 falhas WebSocket de `test_models.py` foram corrigidas separadamente (suíte 166 passed).
- O bug do season (Sintoma 3) é **bidirecional**: o frontend envia float e o backend não valida. O fix precisa cobrir os dois lados.
- O regtest está **travado** (RPC em timeout, IBD há 7.9h). A Fase 1.2 (restart) é urgente.
- O mercado vazio (Sintoma 8) é **consequência** do feed (Sintoma 1) — corrigir o feed resolve a maior parte.
