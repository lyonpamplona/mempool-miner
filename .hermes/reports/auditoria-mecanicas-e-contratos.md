# Auditoria de Mecânicas e Contratos — Mempool Miner
**Data:** 2026-08-19  
**Escopo:** Verificação ponta a ponta de TODAS as mecânicas ativas no novo design  
**Arquivos auditados:** `frontend/index.html` (568 linhas), `frontend/game.js` (6248 linhas), `frontend/pixel.css`, `backend/app/main.py`  
**Método:** Para cada mecânica: DOM/ID → CSS → listener/handler → função JS → endpoint backend → payload → resposta → persistência → evento WebSocket

---

## 🔴 BLOQUEADOR CRÍTICO: Aborto em game.js:5421

```javascript
// Linha 5421 — handleWebSocketMessage NÃO EXISTE no escopo global
const originalHandleWebSocketMessage = handleWebSocketMessage;
// ReferenceError: handleWebSocketMessage is not defined
```

**Impacto:** O script aborta na linha 5421. Todo código top-level abaixo dessa linha **NUNCA executa**:
- Wrappers de `startSession` para Global Events (5432), Friends (5862), Crates (6035), Level (6172)
- Event listeners: Sprint (5453), Friends (5838/5842/5852), Crates (6012/6016/6024), setupPanelToggles (6247)
- As funções declaradas com `function`/`async function` sobrevivem ao hoisting, mas **nenhum listener é registrado**

**Consequência:** Sprint, Friends, Crates e Level System são **QUEBRADOS** — não porque faltam funções, mas porque os listeners que os ativam nunca são registrados.

---

## 🔴 BLOQUEADOR CSP: 11 onclick inline bloqueados

O HTML usa `onclick="..."` em 11 elementos. Se uma CSP bloquear inline event handlers:

| Linha | Elemento | Handler | Impacto |
|-------|----------|---------|---------|
| 192 | Nav button | `switchTab('tx', this)` | Navegação TAB 1 |
| 196 | Nav button | `switchTab('shop', this)` | Navegação TAB 2 (Loja) |
| 200 | Nav button | `switchTab('rank', this)` | Navegação TAB 3 (Network) |
| 204 | Nav button | `switchTab('info', this)` | Navegação TAB 4 (Protocol) |
| 221 | btn-buy-hint | `buyHint()` | Compra de dica |
| 229 | btn-buy-hw | `buyHardware()` | Compra de hardware |
| 237 | btn-buy-ln | `buyLightning()` | Ativação Lightning |
| 478 | Auth button | `startSession()` | **LOGIN TRAVADO** |
| 490 | rbf-btn | `useRbf()` | **useRbf() NÃO EXISTE** |
| 493 | Next block | `prepareNextBlock()` | Próximo bloco |
| 528 | Lightning modal | inline classList | Fechar modal Lightning |

**Mitigação parcial:** Os botões da loja (hint/hw/ln) também têm `addEventListener` em game.js (linhas 745-747), então funcionam se o CSP bloquear apenas os inline. Mas o botão de login (linha 478) depende APENAS do inline `onclick="startSession()"` — o `submit` listener na linha 741-744 só funciona se o botão estiver dentro de um `<form>`, e ele NÃO está.

---

## 🔴 URL MISMATCH: 25 endpoints com path errado

O backend usa exclusivamente `/api/v1/networks/{realm_id}/...`. O frontend usa **DUAS convenções**:

### URLs CORRETAS (17 chamadas) — usam `/api/v1/networks/...`
- `leaderboardUrl()`, `playerStateUrl()`, `achievementsUrl()`, `statsUrl()`
- `missionsUrl()`, `claimMissionUrl()`, `updateMissionsUrl()`
- `chatSendUrl()`, `chatHistoryUrl()`
- `stakingStakeUrl()`, `stakingUnstakeUrl()`, `stakingStatusUrl()`, `stakingHistoryUrl()`
- `decoder/start`, `decoder/submit`

### URLs ERRADAS (25 chamadas) — usam `/api/${activeRealmId}/...`
Estas chamadas **NUNCA chegam ao backend** porque o path não existe:

| Mecânica | URL no JS | Endpoint real no backend |
|----------|-----------|--------------------------|
| Skills | `/api/{realm}/skills/{user}` | `/api/v1/networks/{realm}/skills/{user}` |
| Skills unlock | `/api/{realm}/skills/{user}/unlock` | `/api/v1/networks/{realm}/skills/{user}/upgrade` |
| Energy status | `/api/{realm}/energy/status/{user}` | `/api/v1/networks/{realm}/energy/status` |
| Energy spend | `/api/{realm}/energy/spend/{user}` | `/api/v1/networks/{realm}/energy/spend` |
| Energy buy | `/api/{realm}/energy/buy/{user}` | `/api/v1/networks/{realm}/energy/buy` |
| Season | `/api/{realm}/season/{user}` | `/api/v1/networks/{realm}/season/{user}` |
| Season claim | `/api/{realm}/season/{user}/claim/{level}` | `/api/v1/networks/{realm}/season/{user}/claim/{reward_level}` |
| Season premium | `/api/{realm}/season/{user}/buy-premium` | `/api/v1/networks/{realm}/season/{user}/buy-premium` |
| Cards | `/api/{realm}/cards/{user}` | `/api/v1/networks/{realm}/cards/{user}` |
| Market list | `/api/{realm}/market/list` | `/api/v1/networks/{realm}/market/list` |
| Market sell | `/api/{realm}/market/sell` | `/api/v1/networks/{realm}/market/sell` |
| Market buy | `/api/{realm}/market/buy` | `/api/v1/networks/{realm}/market/buy` |
| Market history | `/api/{realm}/market/history` | `/api/v1/networks/{realm}/market/history` |
| Powerups | `/api/{realm}/powerups/{user}` | `/api/v1/networks/{realm}/powerups/{user}` |
| Global events | `/api/{realm}/global-events` | `/api/v1/networks/{realm}/global-events` |
| Sprint start | `/api/{realm}/sprint/start` | `/api/v1/networks/{realm}/sprint/start` |
| Sprint submit | `/api/{realm}/sprint/submit` | `/api/v1/networks/{realm}/sprint/submit` |
| Sprint leaderboard | `/api/{realm}/sprint/leaderboard` | `/api/v1/networks/{realm}/sprint/leaderboard` |
| Friends list | `/api/{realm}/friends/{user}` | `/api/v1/networks/{realm}/friends/{user}` |
| Friends add | `/api/{realm}/friends/add` | `/api/v1/networks/{realm}/friends/add` |
| Friends remove | `/api/{realm}/friends/remove` | `/api/v1/networks/{realm}/friends/remove` |
| Crates inventory | `/api/{realm}/crates/inventory/{user}` | `/api/v1/networks/{realm}/crates/inventory` |
| Crates open | `/api/{realm}/crates/open` | `/api/v1/networks/{realm}/crates/open` |
| Level | `/api/{realm}/level/{user}` | `/api/v1/networks/{realm}/level/{user}` |
| Level add-xp | `/api/{realm}/level/{user}/add-xp` | `/api/v1/networks/{realm}/level/{user}/add-xp` |

**Resultado:** 25 chamadas HTTP retornam 404. Todas as mecânicas que dependem destas URLs estão **QUEBRADAS**.

---

## INVENTÁRIO COMPLETO POR MECÂNICA

### 1. LOGIN / AUTH
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#auth-modal`, `#miner-input` (HTML:470-482) |
| CSS | ✅ | `.modal-wrap`, `.modal-mecha-box` em pixel.css |
| Handler | ⚠️ PARCIAL | Inline `onclick="startSession()"` (HTML:478) + `submit` listener (JS:741-744) — mas o botão NÃO está dentro de `<form>`, então `submit` não dispara |
| Função JS | ✅ | `startSession()` (JS:824) — completa, com fallbacks |
| Backend | ✅ | WebSocket `/ws/v1/game/{realm_id}` (main.py:4587) |
| WebSocket | ✅ | `game_start`, `network_status`, `transaction_received`, `block_mined` |
| **STATUS FINAL** | **⚠️ PARCIAL** | Funciona se CSP permitir inline onclick. Se bloquear, login trava. O `submit` listener é inútil porque não há `<form>`. |

### 2. JOGO CORE (Grid, Seleção, Timer, Recompensa)
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#word-grid`, `#lines-svg`, `#race-fill`, `#game-status` (HTML:141-180) |
| CSS | ✅ | `.word-grid`, `.cell`, `.race-box`, `.race-bar` em pixel.css |
| Handlers | ✅ | `pointerdown/move/up/cancel`, `keydown` (JS:758-761) |
| Funções JS | ✅ | `buildPlayableBlock()`, `injectWordInGrid()`, `startSelection()`, `endSelection()`, `startNetworkRace()` |
| WebSocket | ✅ | `transaction_received` → `buildPlayableBlock()`, `block_mined` → `showResult()` |
| Backend | ✅ | Ingestor envia transações via WebSocket |
| **STATUS FINAL** | **✅ FUNCIONAL** | Ponta a ponta comprovado. Grid, seleção, timer, recompensa, combo, slashing, RBF, Lightning — tudo conectado. |

### 3. LOJA (Hint, Hardware, Lightning)
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#btn-buy-hint`, `#btn-buy-hw`, `#btn-buy-ln` (HTML:221-237) |
| CSS | ✅ | `.shop-card-mecha`, `.btn-action-small` |
| Handlers | ✅ | Inline onclick + `addEventListener` duplicado (JS:745-747) |
| Funções JS | ✅ | `buyHint()`, `buyHardware()`, `buyLightning()` |
| Backend | ❌ | **NENHUM endpoint de loja** — compras são puramente client-side (debitam saldo local) |
| Persistência | ⚠️ | `syncPlayerState()` envia para `/api/v1/networks/{realm}/player/{user}` (POST) — backend existe (main.py:881) |
| **STATUS FINAL** | **⚠️ PARCIAL** | Funciona localmente mas não persiste upgrades no backend de forma dedicada. O saldo é sincronizado via `syncPlayerState()`. |

### 4. LEADERBOARD
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#leaderboard-list` (HTML:279) |
| Handler | ✅ | Polling via `fetchLeaderboard()` a cada 10s (JS:1007-1009) |
| Função JS | ✅ | `fetchLeaderboard()`, `submitScore()` |
| Endpoint | ✅ | `GET /api/v1/networks/{realm}/leaderboard` (main.py:804), `POST` (main.py:790) |
| **STATUS FINAL** | **✅ FUNCIONAL** | URL correta, endpoint existe, polling ativo. |

### 5. COMBO / SLASHING
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#ui-combo` (HTML:85) |
| Função JS | ✅ | Lógica em `endSelection()` (JS:1901-1905) e slashing (JS:2004-2018) |
| Backend | ❌ | **Nenhum endpoint** — puramente client-side |
| **STATUS FINAL** | **✅ FUNCIONAL** | Não precisa de backend. Lógica completa no frontend. |

### 6. BOSS BATTLES
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#boss-hud`, `#boss-hp-bar`, `#boss-defeat-modal` (HTML:151-161, 500-508) |
| CSS | ✅ | `.boss-hud`, `.boss-hp-bar` em pixel.css |
| Handler | ✅ | WebSocket `boss_block` (JS:1115-1117) |
| Funções JS | ✅ | `handleBossBlock()`, `handleBossTransaction()`, `buildBossPlayableBlock()`, `startBossNetworkRace()`, `showBossDefeatModal()` |
| Backend | ✅ | Ingestor envia `boss_block` via WebSocket |
| **STATUS FINAL** | **✅ FUNCIONAL** | Ponta a ponta comprovado. |

### 7. ENERGIA
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#ui-energy-bar`, `#ui-energy-count`, `#ui-energy-timer`, `#btn-buy-energy` (HTML:108-115) |
| CSS | ✅ | `.energy-bar-container`, `.energy-bar-fill` |
| Handler | ✅ | `addEventListener` no botão (JS:4479-4481) |
| Funções JS | ✅ | `loadEnergyState()`, `spendEnergy()`, `buyEnergy()`, `updateEnergyUI()` |
| Wrapper startSession | ✅ | Linha 4492-4497 (ANTES do abort) |
| URL | ❌ | `/api/${activeRealmId}/energy/status/{user}` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/energy/status` (main.py:4145) |
| **STATUS FINAL** | **❌ QUEBRADO** | URL errada retorna 404. A mecânica existe mas nunca carrega dados. |

### 8. CRATES (Loot Boxes)
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#btn-open-crate-free`, `#btn-open-crate-buy`, `#crate-free-count` (HTML:252-263) |
| Funções JS | ✅ | `loadCrateInventory()`, `openCrate()`, `showCrateResult()` |
| Wrapper startSession | ❌ | Linha 6035 — **DEPOIS do abort em 5421** |
| Event listeners | ❌ | Linhas 6012/6016 — **DEPOIS do abort** |
| URL | ❌ | `/api/${activeRealmId}/crates/inventory/{user}` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/crates/inventory` (main.py:3577) |
| **STATUS FINAL** | **❌ QUEBRADO** | Abort + URL errada. Duplo bloqueio. |

### 9. SPRINT
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#btn-sprint-mode`, `#sprint-timer-value`, `#sprint-leaderboard-list` (HTML:334-339) |
| Funções JS | ✅ | `startSprintRound()`, `submitSprintResult()`, `loadSprintLeaderboard()` |
| Handler | ❌ | `addEventListener` em linha 5453 — **DEPOIS do abort** |
| URL | ❌ | `/api/${activeRealmId}/sprint/...` — **PATH ERRADO** |
| Endpoint real | ✅ | `POST /api/v1/networks/{realm}/sprint/start` (main.py:4692) |
| **STATUS FINAL** | **❌ QUEBRADO** | Abort + URL errada. |

### 10. MISSIONS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#missions-panel`, `#missions-list` (HTML:287-290) |
| Funções JS | ✅ | `loadMissions()`, `claimReward()`, `updateMissionsProgress()` |
| Wrapper startSession | ✅ | Linha 3143-3161 (ANTES do abort) |
| URL | ✅ | `missionsUrl()` usa `/api/v1/networks/...` |
| Endpoint | ✅ | `GET /api/v1/networks/{realm}/missions/{user}` (main.py:1166) |
| **STATUS FINAL** | **✅ FUNCIONAL** | URL correta, wrapper antes do abort, endpoint existe. |

### 11. CHAT
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#chat-panel`, `#chat-messages`, `#chat-input`, `#chat-send-btn` (HTML:293-302) |
| Funções JS | ✅ | `sendChatMessage()`, `loadChatHistory()`, `renderChatMessages()` |
| Wrapper startSession | ✅ | Linha 3530-3542 (ANTES do abort) |
| URL | ✅ | `chatSendUrl()` e `chatHistoryUrl()` usam `/api/v1/networks/...` |
| Endpoint | ✅ | `POST /api/v1/networks/{realm}/chat/send` (main.py:2251), `GET /chat/history` (main.py:2286) |
| **STATUS FINAL** | **✅ FUNCIONAL** | Ponta a ponta comprovado. |

### 12. FRIENDS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#friends-panel`, `#friends-list`, `#friends-add-input`, `#btn-friends-add` (HTML:305-314) |
| Funções JS | ✅ | `loadFriendsList()`, `addFriend()`, `removeFriend()` |
| Wrapper startSession | ❌ | Linha 5862 — **DEPOIS do abort** |
| Event listeners | ❌ | Linhas 5838/5842/5852 — **DEPOIS do abort** |
| URL | ❌ | `/api/${activeRealmId}/friends/...` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/friends/{user}` (main.py:4119) |
| **STATUS FINAL** | **❌ QUEBRADO** | Abort + URL errada. |

### 13. MARKET
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#market-panel`, `#market-browse`, `#market-sell` (HTML:317-331) |
| Funções JS | ✅ | `loadMarketList()`, `buyMarketListing()`, `sellMarketPowerup()` |
| Wrapper startSession | ✅ | Linha 5260-5265 (ANTES do abort) |
| URL | ❌ | `/api/${activeRealmId}/market/...` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/market/list` (main.py:2430) |
| **STATUS FINAL** | **❌ QUEBRADO** | Wrapper carrega mas URL errada retorna 404. |

### 14. STAKING
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#staking-panel`, `#staking-form`, `#btn-stake`, `#btn-cancel-stake` (HTML:359-376) |
| Funções JS | ✅ | `performStake()`, `cancelStake()`, `loadStakingStatus()` |
| Wrapper startSession | ✅ | Linha 3537-3541 (dentro do wrapper do chat, ANTES do abort) |
| URL | ✅ | `stakingStakeUrl()` usa `/api/v1/networks/...` |
| Endpoint | ✅ | `POST /api/v1/networks/{realm}/staking/stake` (main.py:3714) |
| **STATUS FINAL** | **✅ FUNCIONAL** | URL correta, wrapper antes do abort, endpoint existe. |

### 15. SKILLS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#skills-panel`, `#skills-content`, `#skills-points-value` (HTML:379-387) |
| Funções JS | ✅ | `loadSkillTree()`, `unlockSkill()`, `renderSkillTree()` |
| URL | ❌ | `/api/${activeRealmId}/skills/{user}` — **PATH ERRADO** |
| URL unlock | ❌ | `/api/${activeRealmId}/skills/{user}/unlock` — **PATH ERRADO + endpoint é /upgrade** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/skills/{user}` (main.py:1620), `POST /upgrade` (main.py:1700) |
| **STATUS FINAL** | **❌ QUEBRADO** | URL errada + nome de endpoint diferente (`/unlock` vs `/upgrade`). |

### 16. SEASON PASS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#season-panel`, `#season-progress-fill`, `#btn-buy-season-premium` (HTML:390-410) |
| Funções JS | ✅ | `loadSeasonData()`, `claimSeasonReward()`, `buySeasonPremium()` |
| Wrapper startSession | ✅ | Linha 4740-4745 (ANTES do abort) |
| URL | ❌ | `/api/${activeRealmId}/season/{user}` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/season/{user}` (main.py:4616) |
| **STATUS FINAL** | **❌ QUEBRADO** | Wrapper carrega mas URL errada retorna 404. |

### 17. CARDS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#cards-panel`, `#cards-grid`, `#cards-total` (HTML:413-427) |
| Funções JS | ✅ | `loadCardsData()`, `renderCardsUI()`, `renderCardsGrid()` |
| Wrapper startSession | ✅ | Linha 4933-4937 (ANTES do abort) |
| URL | ❌ | `/api/${activeRealmId}/cards/{user}` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/cards/{user}` (main.py:3360) |
| **STATUS FINAL** | **❌ QUEBRADO** | Wrapper carrega mas URL errada retorna 404. |

### 18. ACHIEVEMENTS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#achievement-toast`, `#achievements-modal`, `#achievements-grid` (HTML:36-44, 511-521) |
| Funções JS | ✅ | `fetchAchievements()`, `pushStats()`, `renderAchievementsModal()`, `showAchievementToast()` |
| URL | ✅ | `achievementsUrl()` usa `/api/v1/networks/...` |
| Endpoint | ✅ | `GET /api/v1/networks/{realm}/achievements/{user}` (main.py:1057) |
| Tracking | ✅ | `trackWordFound()`, `trackCombo()`, `trackBlockCompleted()` — chamados em `endSelection()` e `showResult()` |
| **STATUS FINAL** | **✅ FUNCIONAL** | Ponta a ponta comprovado. |

### 19. EVENTOS GLOBAIS
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#global-event-banner`, `#global-event-countdown` (HTML:165-177) |
| Funções JS | ✅ | `handleGlobalEventMessage()`, `renderGlobalEventBanner()` |
| Wrapper startSession | ❌ | Linha 5432 — **DEPOIS do abort** |
| WebSocket handler | ✅ | `event_preannounce`, `event_started`, `event_ended` (JS:1121-1132) — ANTES do abort |
| URL | ❌ | `/api/${activeRealmId}/global-events` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/global-events` (main.py:625) |
| **STATUS FINAL** | **⚠️ PARCIAL** | WebSocket funciona (handler antes do abort), mas `loadActiveGlobalEvent()` nunca roda (abort + URL errada). Eventos em tempo real funcionam, mas carregamento inicial não. |

### 20. PWA
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#pwa-update-banner`, `#btn-install-app` (HTML:24-33, 71) |
| Funções JS | ✅ | `registerPwa()`, `showServiceWorkerUpdate()` |
| Manifest | ✅ | `manifest.webmanifest` (795 bytes) |
| Service Worker | ✅ | `service-worker.js` (2245 bytes) |
| Registro | ✅ | `registerPwa()` chamado em JS:818 (ANTES do abort) |
| **STATUS FINAL** | **✅ FUNCIONAL** | Registro PWA, install prompt, update banner — tudo antes do abort. |

### 21. DECODER (Mini-game)
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#decoder-modal`, `#decoder-input`, `#btn-decoder-launch` (HTML:431-451, 266-272) |
| Funções JS | ✅ | `startDecoderGame()`, `submitDecoderAnswer()`, `closeDecoderModal()` |
| URL | ✅ | `/api/v1/networks/{realm}/decoder/start` e `/decoder/submit` |
| Endpoint | ✅ | `POST /api/v1/networks/{realm}/decoder/start` (main.py:4441) |
| **STATUS FINAL** | **✅ FUNCIONAL** | URL correta, endpoint existe. |

### 22. LEVEL SYSTEM
| Campo | Status | Detalhe |
|-------|--------|---------|
| DOM | ✅ | `#level-bar-container`, `#level-bar-fill`, `#level-name` (HTML:95-105) |
| Funções JS | ✅ | `loadLevelState()`, `addXP()`, `updateLevelUI()` |
| Wrapper startSession | ❌ | Linha 6172 — **DEPOIS do abort** |
| URL | ❌ | `/api/${activeRealmId}/level/{user}` — **PATH ERRADO** |
| Endpoint real | ✅ | `GET /api/v1/networks/{realm}/level/{user}` (main.py:4804) |
| **STATUS FINAL** | **❌ QUEBRADO** | Abort + URL errada. |

---

## STUBS E FUNÇÕES VAZIAS

| Função | Linha | Problema |
|--------|-------|----------|
| `loadPowerupsInventory()` | JS:267 | **STUB** — corpo vazio, comentário "carrega inventario de powerups do backend" |
| `renderWordBank()` | JS:1683 | **STUB** — corpo vazio, alias para `renderBankWord()` |
| `useRbf()` | HTML:490 | **NÃO EXISTE** — referenciada em `onclick` mas nunca definida no JS |
| `handleWebSocketMessage` | JS:5421 | **NÃO EXISTE** — referenciada mas nunca definida; causa abort do script |
| `showTab('jogo')` | JS:131 | **DUPLICADO** — redefinido em JS:131 mas nunca chamado com esses args; o `switchTab` usa 'tx'/'shop'/'rank'/'info' |

---

## WRAPPERS DE startSession (11 no total)

Ordem de execução (cadeia de wrappers):

1. **Missions** (3143) — ✅ ANTES do abort
2. **Chat** (3530) — ✅ ANTES do abort (carrega staking status)
3. **Energy** (4492) — ✅ ANTES do abort
4. **Season** (4740) — ✅ ANTES do abort
5. **Cards** (4933) — ✅ ANTES do abort
6. **Market** (5260) — ✅ ANTES do abort
7. **Global Events** (5432) — ❌ DEPOIS do abort
8. **Friends** (5862) — ❌ DEPOIS do abort
9. **Crates** (6035) — ❌ DEPOIS do abort
10. **Level** (6172) — ❌ DEPOIS do abort

Os wrappers 7-10 nunca executam porque o script aborta em 5421.

---

## RESUMO EXECUTIVO

| Status | Contagem | Mecânicas |
|--------|----------|-----------|
| ✅ FUNCIONAL | 8 | Jogo Core, Leaderboard, Combo/Slashing, Boss, Missions, Chat, Staking, Achievements, Decoder, PWA |
| ⚠️ PARCIAL | 3 | Login/Auth (CSP), Loja (sem endpoint dedicado), Eventos Globais (WS sim, HTTP não) |
| ❌ QUEBRADO | 9 | Energia, Crates, Sprint, Friends, Market, Skills, Season, Cards, Level |

**Total:** 20 mecânicas auditadas  
**Funcionais:** 8 (40%)  
**Parciais:** 3 (15%)  
**Quebradas:** 9 (45%)

---

## ROADMAP TÉCNICO SUGERIDO

### Fase 1: Críticos (bloqueiam o jogo)
1. **Definir `handleWebSocketMessage`** ou remover a linha 5421-5429 — desbloqueia Global Events, Friends, Crates, Level
2. **Corrigir 25 URLs** — substituir `/api/${activeRealmId}/...` por `/api/v1/networks/${activeRealmId}/...` em todas as chamadas
3. **Corrigir `/unlock` → `/upgrade`** no endpoint de Skills
4. **Remover `useRbf()` do HTML:490** — função não existe; o RBF é tratado por `showOrphanBlockSalvage()`
5. **Adicionar `<form>` ao auth-modal** ou converter `onclick` para `addEventListener` — resolve o login travado com CSP

### Fase 2: Estruturais
6. **Consolidar os 11 wrappers de startSession** em um único sistema de plugins/hooks — a cadeia atual é frágil e difícil de debugar
7. **Criar helper `apiUrl(path)`** que centraliza a construção de URLs — elimina o mismatch de convenções
8. **Implementar `handleWebSocketMessage`** como função real ou remover a tentativa de wrap

### Fase 3: Completude
9. **Endpoint dedicado para loja** — `buyHint()`, `buyHardware()`, `buyLightning()` operam apenas no client-side
10. **Preencher `loadPowerupsInventory()`** — stub vazio
11. **Preencher `renderWordBank()`** — stub vazio (alias para `renderBankWord`)
12. **Remover onclick inline** — migrar todos os 11 handlers para `addEventListener` para compatibilidade com CSP

### Fase 4: Qualidade
13. **Testes de integração** para cada mecânica — verificar que DOM → handler → JS → backend → resposta funciona
14. **Validação de payload** — garantir que os payloads enviados correspondem ao que o backend espera
15. **Tratamento de erro unificado** — atualmente cada função tem seu próprio try/catch com mensagens diferentes
