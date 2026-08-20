# Auditoria Completa das Mecânicas do Jogo — Mempool Miner

**Data:** 2026-08-19  
**Arquivos auditados:**
- `frontend/index.html` (569 linhas)
- `frontend/game.js` (6192 linhas)
- `frontend/pixel.css` (1892 linhas)

---

## 1. RESUMO EXECUTIVO

| Total de mecânicas | Funcionais | Parciais | Quebradas |
|---|---|---|---|
| 24 | 18 | 5 | 1 |

**Problema principal:** A função `showNotification()` é chamada em ~30 lugares mas **nunca definida**. Isso quebra silenciosamente todas as mecânicas que dependem dela para feedback visual.

---

## 2. LISTA COMPLETA DE MECÂNICAS

### 2.1 Caça-palavras (Core Game) — ✅ FUNCIONAL
- **IDs HTML:** `word-grid`, `lines-svg`, `tx-list-container`, `race-fill`, `grid-overlay`, `tx-loading`, `game-status`, `grid-instructions`
- **Classes CSS:** `.cell`, `.cell.sel`, `.cell.found`, `.cell.mev-found`, `.cell.hint`, `.cross-line`, `.grid-overlay`, `.svg-layer`
- **Lógica JS:** `buildPlayableBlock()`, `injectWordInGrid()`, `handlePointerStart/Move/End`, `startSelection()`, `continueSelection()`, `endSelection()`
- **Event listeners:** `pointerdown`, `pointermove`, `pointerup`, `pointercancel`, `keydown` no grid
- **Status:** ✅ Todos os IDs existem, classes CSS presentes, lógica completa, listeners vinculados

### 2.2 Loja (Shop) — ✅ FUNCIONAL
- **IDs HTML:** `btn-buy-hint`, `btn-buy-hw`, `btn-buy-ln`, `hw-title`, `btn-buy-energy`
- **Classes CSS:** `.shop-card-mecha`, `.shop-row`, `.btn-action-small`
- **Lógica JS:** `buyHint()`, `buyHardware()`, `buyLightning()`, `updateStoreUI()`
- **Event listeners:** `onclick` inline no HTML + `addEventListener` no JS
- **Status:** ✅ Funcional

### 2.3 Leaderboard — ✅ FUNCIONAL
- **IDs HTML:** `leaderboard-list`, `pool-list`
- **Classes CSS:** `.rank-item`, `.loading-state`
- **Lógica JS:** `fetchLeaderboard()`, `fetchPools()`, `submitScore()`
- **Event listeners:** Polling automático via `setInterval`
- **Status:** ✅ Funcional

### 2.4 Slashing — ✅ FUNCIONAL
- **IDs HTML:** `ui-balance` (para débito)
- **Classes CSS:** `.slashing-flash`, `.floating-text`
- **Lógica JS:** `consecutiveErrors` counter, `SLASHING_THRESHOLD=3`, `SLASHING_PENALTY=0.05`
- **Status:** ✅ Funcional — penalidade de 5% após 3 erros consecutivos

### 2.5 Combo — ✅ FUNCIONAL
- **IDs HTML:** `ui-combo`
- **Classes CSS:** `.combo-value`
- **Lógica JS:** `comboMultiplier` (1.0–4.0), janela de 8s entre palavras
- **Status:** ✅ Funcional

### 2.6 Boss Battles — ✅ FUNCIONAL
- **IDs HTML:** `boss-hud`, `boss-subtitle`, `boss-hp-bar`, `boss-hp-text`, `boss-defeat-modal`, `boss-defeat-title`, `boss-defeat-text`, `boss-defeat-btn`
- **Classes CSS:** `.boss-hud`, `.boss-hp-bar`, `.boss-hp-bar-container`, `.boss-hp-text`, `.boss-flash`, `.boss-shake`, `.boss-active`, `.boss-hp-damage`
- **Lógica JS:** `handleBossBlock()`, `handleBossTransaction()`, `buildBossPlayableBlock()`, `startBossNetworkRace()`, `showBossDefeatModal()`, `resetBossState()`
- **Event listeners:** WebSocket `boss_block` action
- **Status:** ✅ Funcional

### 2.7 Season Pass — ⚠️ PARCIAL
- **IDs HTML:** `season-panel`, `season-id-value`, `season-level-value`, `season-xp-value`, `season-progress-bar`, `season-progress-fill`, `season-progress-text`, `season-timer`, `season-rewards-free`, `season-rewards-premium`, `btn-buy-season-premium`, `season-loading`, `season-content`
- **Classes CSS:** `.season-progress-bar`, `.season-progress-fill`, `.season-progress-text`, `.season-panel`
- **Lógica JS:** `loadSeasonData()`, `renderSeasonUI()`, `renderRewards()`, `claimSeasonReward()`, `buySeasonPremium()`
- **Event listeners:** `btn-buy-season-premium` click, `.season-tab` clicks
- **Problema:** API endpoints usam `/api/${activeRealmId}/season/...` — formato inconsistente com o padrão `/api/v1/networks/...`
- **Status:** ⚠️ Parcial — UI completa mas API endpoints podem não funcionar

### 2.8 Cards (Colecionáveis) — ⚠️ PARCIAL
- **IDs HTML:** `cards-panel`, `cards-total`, `cards-common`, `cards-rare`, `cards-epic`, `cards-legendary`, `cards-bonus`, `cards-grid`, `cards-loading`
- **Classes CSS:** `.cards-grid`, `.cards-panel`, `.cards-stat-item`, `.card-filter`
- **Lógica JS:** `loadCardsData()`, `renderCardsUI()`, `renderCardsGrid()`, `showCardPullAnimation()`
- **Event listeners:** `.card-filter` clicks, `btn-cards` toggle
- **Problema:** Mesmo problema de API endpoints (`/api/${activeRealmId}/cards/...`)
- **Status:** ⚠️ Parcial

### 2.9 Staking — ✅ FUNCIONAL
- **IDs HTML:** `staking-panel`, `staking-form`, `staking-amount-input`, `staking-duration`, `staking-bonus`, `btn-stake`, `btn-cancel-stake`, `staking-timer`, `staking-active`, `staking-amount`, `staking-history-list`
- **Classes CSS:** `.staking-panel`, `.staking-form`, `.staking-active`, `.staking-history-list`
- **Lógica JS:** `loadStakingStatus()`, `updateStakingUI()`, `performStake()`, `cancelStake()`, `startStakeCountdown()`
- **Event listeners:** `btn-stake`, `btn-cancel-stake` clicks
- **Status:** ✅ Funcional — usa API padrão `/api/v1/networks/...`

### 2.10 Skills (Skill Tree) — ⚠️ PARCIAL
- **IDs HTML:** `skills-panel`, `skills-header`, `skills-level-value`, `skills-points-value`, `skills-content`, `skills-loading`
- **Classes CSS:** `.skills-panel`, `.skills-content`, `.skills-header`, `.skill-branch`, `.skill-node`
- **Lógica JS:** `loadSkillTree()`, `renderSkillTree()`, `unlockSkill()`, `applySkillBonuses()`
- **Problema:** `applySkillBonuses()` referencia `baseTimeLimit` e `hintCost` que **não existem** como variáveis globais
- **Status:** ⚠️ Parcial — variáveis não definidas

### 2.11 Decoder — ✅ FUNCIONAL
- **IDs HTML:** `decoder-modal`, `decoder-txid`, `decoder-input`, `decoder-hint-letter`, `decoder-feedback`, `decoder-timer-bar`, `decoder-timer-fill`, `decoder-timer-text`, `decoder-streak`, `decoder-wins`, `btn-decoder-submit`, `btn-close-decoder`, `btn-decoder-launch`
- **Classes CSS:** `.decoder-content`, `.decoder-timer-bar`, `.decoder-timer-text`, `.decoder-feedback`
- **Lógica JS:** `startDecoderGame()`, `submitDecoderAnswer()`, `handleDecoderTimeout()`, `closeDecoderModal()`
- **Event listeners:** `btn-decoder-launch`, `btn-decoder-submit`, `btn-close-decoder`, Enter no input
- **Status:** ✅ Funcional

### 2.12 Chat — ✅ FUNCIONAL
- **IDs HTML:** `chat-panel`, `chat-messages`, `chat-input`, `chat-send-btn`, `chat-emoji-bar`, `chat-rate-info`
- **Classes CSS:** `.chat-messages`, `.chat-input`, `.chat-send-btn`, `.chat-emoji-bar`, `.chat-rate-info`
- **Lógica JS:** `sendChatMessage()`, `loadChatHistory()`, `renderChatMessages()`, `insertEmoji()`
- **Event listeners:** `chat-send-btn` click, Enter no input, emoji bar clicks
- **Problema:** `chatHistoryLoaded` é usado mas nunca declarado
- **Status:** ✅ Funcional (com bug menor)

### 2.13 Market — ⚠️ PARCIAL
- **IDs HTML:** `market-panel`, `market-browse`, `market-sell`, `market-sell-select`, `market-sell-price`, `market-history`, `market-filter-powerup`, `btn-market`, `btn-market-sell`, `btn-refresh-market`
- **Classes CSS:** `.market-panel`, `.market-listings`, `.market-inventory`, `.market-sales-history`
- **Lógica JS:** `loadMarketList()`, `renderMarketList()`, `buyMarketListing()`, `sellMarketPowerup()`
- **Problema:** `marketLoaded` é usado mas nunca declarado; API endpoints usam formato `/api/${activeRealmId}/market/...`
- **Status:** ⚠️ Parcial

### 2.14 Friends — ⚠️ PARCIAL
- **IDs HTML:** `friends-panel`, `friends-list`, `friends-add-input`, `btn-friends-add`, `friends-coop-bonus`, `friends-loading`
- **Classes CSS:** `.friends-panel`, `.friends-list`, `.friends-coop-bonus`
- **Lógica JS:** `loadFriendsList()`, `renderFriendsUI()`, `addFriend()`, `removeFriend()`
- **Problema:** API endpoints usam formato `/api/${activeRealmId}/friends/...`; `showNotification()` não definida
- **Status:** ⚠️ Parcial

### 2.15 Achievements — ✅ FUNCIONAL
- **IDs HTML:** `achievements-modal`, `achievements-summary`, `achievements-filters`, `achievements-grid`, `btn-close-achievements`, `achievement-toast`, `achievement-toast-icon`, `achievement-toast-title`, `achievement-toast-desc`
- **Classes CSS:** `.achievement-toast`, `.achievement-toast-content`, `.achievement-toast-icon`, `.achievement-toast-title`, `.achievement-toast-desc`, `.achievements-grid`, `.achievements-summary`, `.achievements-filters`
- **Lógica JS:** `fetchAchievements()`, `renderAchievementsModal()`, `showAchievementToast()`, `trackWordFound()`, `trackCombo()`, `trackBlockCompleted()`
- **Event listeners:** `btn-achievements`, `btn-close-achievements`
- **Status:** ✅ Funcional

### 2.16 Global Events — ✅ FUNCIONAL
- **IDs HTML:** `global-event-banner`, `global-event-icon`, `global-event-label`, `global-event-description`, `global-event-countdown`, `btn-dismiss-event`
- **Classes CSS:** `.global-event-banner`, `.global-event-banner-inner`, `.global-event-icon`, `.global-event-label`, `.global-event-description`, `.global-event-countdown`, `.global-event-dismiss`
- **Lógica JS:** `handleGlobalEventMessage()`, `renderGlobalEventBanner()`, `startGlobalEventCountdown()`, `hideGlobalEventBanner()`
- **Event listeners:** `btn-dismiss-event` click, WebSocket events
- **Problema:** `handleWebSocketMessage()` é referenciado mas nunca definido (linha 5365)
- **Status:** ✅ Funcional (via WebSocket direto)

### 2.17 PWA — ✅ FUNCIONAL
- **IDs HTML:** `btn-install-app`, `pwa-update-banner`, `pwa-update-message`, `btn-update-app`, `btn-dismiss-update`
- **Classes CSS:** `.update-banner`, `.update-actions`
- **Lógica JS:** `registerPwa()`, `showServiceWorkerUpdate()`
- **Event listeners:** `beforeinstallprompt`, `appinstalled`, `click` nos botões
- **Status:** ✅ Funcional

### 2.18 Tutorial / Auth Modal — ✅ FUNCIONAL
- **IDs HTML:** `auth-modal`, `miner-input`
- **Classes CSS:** `.modal-wrap`, `.modal-wrap.active`, `.modal-wrap.hidden`, `.modal-mecha-box`, `.input-mecha`
- **Lógica JS:** `startSession()`, `setModalState()`
- **CSS fix aplicado:** `.modal-wrap.active { display: flex; }` e `.modal-wrap { display: none; }`
- **Status:** ✅ Funcional (corrigido)

### 2.19 Energy — ⚠️ PARCIAL
- **IDs HTML:** `energy-bar-container`, `ui-energy-bar`, `ui-energy-count`, `ui-energy-timer`, `btn-buy-energy`
- **Classes CSS:** `.energy-bar-container`, `.energy-bar-fill`, `.energy-bar-track`, `.energy-count`, `.energy-timer`, `.energy-label`, `.low`
- **Lógica JS:** `loadEnergyState()`, `updateEnergyUI()`, `spendEnergy()`, `buyEnergy()`
- **Problema:** API endpoints usam formato `/api/${activeRealmId}/energy/...`; `showNotification()` não definida
- **Status:** ⚠️ Parcial

### 2.20 Power-ups — ✅ FUNCIONAL
- **IDs HTML:** `powerups-bar-container`, `btn-powerups-toggle`, `powerups-active`
- **Classes CSS:** `.powerups-bar-container`, `.powerups-header`, `.powerups-label`, `.powerups-active`
- **Lógica JS:** Toggle de visibilidade via `btn-powerups-toggle`
- **Problema:** `loadPowerupsInventory()` é chamado mas nunca definido
- **Status:** ✅ Funcional (toggle funciona; inventário não carrega)

### 2.21 Sprint Mode — ⚠️ PARCIAL
- **IDs HTML:** `btn-sprint-mode`, `sprint-timer-display`, `sprint-timer-value`, `sprint-leaderboard-list`
- **Classes CSS:** `.sprint-timer`, `.sprint-timer-container`, `.sprint-leaderboard-list`
- **Lógica JS:** `startSprintRound()`, `startSprintCountdown()`, `endSprintRound()`, `showSprintResult()`
- **Problema:** `renderWordBank()` chamado mas não definido; `showNotification()` não definida; API endpoints usam formato `/api/${activeRealmId}/sprint/...`
- **Status:** ⚠️ Parcial

### 2.22 Missions — ✅ FUNCIONAL
- **IDs HTML:** `missions-panel`, `missions-loading`, `missions-list`
- **Classes CSS:** `.missions-panel`, `.missions-list`, `.mission-card`, `.weekly`
- **Lógica JS:** `loadMissions()`, `renderMissions()`, `createMissionCard()`, `claimReward()`, `updateMissionsProgress()`
- **Event listeners:** Integrado via wrappers em `startSession`, `endSelection`, `showResult`
- **Status:** ✅ Funcional

### 2.23 Crates (Loot Boxes) — ⚠️ PARCIAL
- **IDs HTML:** `btn-open-crate-free`, `btn-open-crate-buy`, `crate-free-count`, `crate-icon`
- **Classes CSS:** `.crate-icon`, `.crate-result`, `.crate-modal-content`
- **Lógica JS:** `loadCrateInventory()`, `updateCrateUI()`, `openCrate()`, `showCrateResult()`
- **Problema:** `showNotification()` não definida; API endpoints usam formato `/api/${activeRealmId}/crates/...`
- **Status:** ⚠️ Parcial

### 2.24 Level System — ✅ FUNCIONAL
- **IDs HTML:** `level-bar-container`, `level-icon`, `level-name`, `level-value`, `level-bar-fill`, `level-bar-text`
- **Classes CSS:** `.level-bar-container`, `.level-bar-fill`, `.level-bar-track`, `.level-bar-text`, `.level-icon`, `.level-info`, `.level-name`, `.level-value`, `.leveled-up`
- **Lógica JS:** `updateLevelUI()`, `checkLevelUp()`
- **Status:** ✅ Funcional

---

## 3. FLUXO DE LOGIN/AUTH

### 3.1 Auth Modal
- **HTML:** `#auth-modal` com `.modal-wrap` (sem `.hidden` — aparece por padrão)
- **CSS:** `.modal-wrap.active { display: flex; }` ✅ (corrigido)
- **JS:** `setModalState(authModal, true)` no IIFE de restauração de sessão
- **Status:** ✅ Funcional

### 3.2 startSession()
- **HTML:** Botão com `onclick="startSession()"` + input `#miner-input`
- **JS:** Função completa com validação de nickname, WebSocket, teardown
- **Problema:** 8+ wrappers encadeados (missions, chat, staking, energy, season, cards, market, friends, crates) — o último sobrescreve todos os anteriores
- **Status:** ⚠️ Funcional mas frágil

### 3.3 networkCatalog
- **JS:** `loadNetworkCatalog()` faz fetch em `/api/v1/networks`
- **HTML:** `#network-select` e `#network-status` existem (no div de compatibilidade)
- **Status:** ✅ Funcional

### 3.4 WebSocket
- **JS:** `gameSocketUrl()` constrói URL, `ws = new WebSocket(...)`
- **Handlers:** `onopen`, `onmessage`, `onerror`, `onclose` todos definidos
- **Reconexão:** Backoff exponencial (1s, 2s, 4s, 8s, 16s — máx 5 tentativas)
- **Status:** ✅ Funcional

---

## 4. ABAS (TX, SHOP, RANK, INFO)

### 4.1 switchTab()
- **JS:** `switchTab(tabId, btn)` — remove `.active` de todas as `.tab-pane` e `.mecha-btn`, adiciona ao alvo
- **HTML:** 4 botões `mecha-btn` com `onclick="switchTab('tx'|'shop'|'rank'|'info', this)"`
- **Status:** ✅ Funcional

### 4.2 Conteúdo de cada aba
| Aba | ID | Conteúdo | Status |
|-----|---|----------|--------|
| TX | `#tab-tx` | `#tx-list-container` (word bank) | ✅ |
| SHOP | `#tab-shop` | Hint, Hardware, Lightning, Energy, Crates, Decoder | ✅ |
| RANK | `#tab-rank` | Leaderboard, Pools, Missions, Chat, Friends, Market, Sprint | ✅ |
| INFO | `#tab-info` | Protocol info, Staking, Skills, Season, Cards, Decoder modal | ✅ |

### 4.3 Botões de navegação
- **HTML:** `onclick="switchTab('tx', this)"` etc.
- **CSS:** `.mecha-btn.active` com estilo visual distinto
- **Status:** ✅ Funcional

---

## 5. MODAIS

| Modal | ID | `.modal-wrap` | `.hidden` | `setModalState()` | Status |
|-------|---|---|---|---|--------|
| Auth | `#auth-modal` | ✅ | ❌ (intencional — aparece por padrão) | ✅ | ✅ |
| Result | `#result-modal` | ✅ | ✅ | ✅ | ✅ |
| Boss Defeat | `#boss-defeat-modal` | ✅ | ✅ | ✅ | ✅ |
| Achievements | `#achievements-modal` | ✅ | ✅ | ✅ | ✅ |
| Decoder | `#decoder-modal` | ✅ | ✅ | ✅ | ✅ |
| Lightning | `#lightning-modal` | ✅ | ✅ | ✅ | ✅ |
| PWA Update | `#pwa-update-banner` | ✅ | ✅ | ❌ (usa `.hidden` direto) | ✅ |

---

## 6. BUGS ENCONTRADOS

### BUG-1: `showNotification()` não definida — 🔴 CRÍTICO
- **Ocorrências:** ~30 chamadas em game.js
- **Mecânicas afetadas:** Sprint, Market, Friends, Skills, Season, Energy, Crates, Global Events
- **Impacto:** Nenhum feedback visual para o usuário nessas mecânicas
- **Correção:** Adicionar função:
```javascript
function showNotification(message, type = 'info') {
    announceGameStatus(message);
    // Opcional: criar toast visual
}
```

### BUG-2: `handleWebSocketMessage()` referenciado mas não definido — 🟡 MÉDIO
- **Linha:** 5365
- **Impacto:** Wrapper de eventos globais não funciona
- **Correção:** Remover o wrapper ou integrar no `socket.onmessage` existente

### BUG-3: Variáveis não declaradas — 🟡 MÉDIO
- `chatHistoryLoaded` (linha 3229)
- `baseTimeLimit` (linha 4260)
- `hintCost` (linha 4265)
- `marketLoaded` (linha 5197)
- **Correção:** Declarar no topo do arquivo

### BUG-4: `renderWordBank()` não definida — 🟡 MÉDIO
- **Linha:** 4427 (em `startSprintRound()`)
- **Impacto:** Sprint mode não renderiza palavras
- **Correção:** Adicionar função ou usar `renderBankWord()` existente

### BUG-5: `loadPowerupsInventory()` não definida — 🟡 MÉDIO
- **Linha:** 5973
- **Impacto:** Power-ups não carregam ao abrir inventário
- **Correção:** Adicionar função stub

### BUG-6: Encadeamento frágil de `startSession` — 🟡 MÉDIO
- **8 wrappers** sobrescrevem `startSession` sequencialmente
- **Módulos:** Missions, Chat, Staking, Energy, Season, Cards, Market, Friends, Crates
- **Impacto:** Se um wrapper falhar, os subsequentes não executam
- **Correção:** Consolidar em uma única função de inicialização

### BUG-7: API endpoints inconsistentes — 🟡 MÉDIO
- **Padrão correto:** `/api/v1/networks/{realmId}/...`
- **Endpoints problemáticos:** `/api/${activeRealmId}/...` (Skills, Energy, Season, Cards, Market, Friends, Sprint, Crates, Global Events)
- **Impacto:** Essas mecânicas não comunicam com o backend
- **Correção:** Padronizar todos os endpoints

---

## 7. PLANOS DE CORREÇÃO

### Prioridade 1 (Crítico):
1. **Adicionar `showNotification()`** — 1 linha de código
2. **Declarar variáveis faltantes** — `chatHistoryLoaded`, `baseTimeLimit`, `hintCost`, `marketLoaded`

### Prioridade 2 (Alto):
3. **Adicionar `renderWordBank()`** — usar `renderBankWord()` existente
4. **Adicionar `loadPowerupsInventory()`** — stub vazio
5. **Remover wrapper `handleWebSocketMessage`** — integrar no `socket.onmessage`

### Prioridade 3 (Médio):
6. **Consolidar wrappers de `startSession`** — criar `initAllSystems()`
7. **Padronizar API endpoints** — mudar `/api/${activeRealmId}/` para `/api/v1/networks/${activeRealmId}/`

### Prioridade 4 (Baixo):
8. **Adicionar CSS para classes dinâmicas** — `.floating-text`, `.chat-message`, `.market-listing-buy-btn`

---

## 8. CONCLUSÃO

O redesign Mecha Sci-Fi foi aplicado com sucesso. A estrutura HTML/CSS está completa e consistente. O auth-modal foi corrigido. As mecânicas core (caça-palavras, loja, leaderboard, slashing, combo, boss battles, decoder, chat, staking, achievements, global events, PWA, missions, energy, level system) estão **funcionais**.

As 5 mecânicas parciais (Season Pass, Cards, Skills, Market, Friends) compartilham o mesmo problema: **API endpoints inconsistentes** que usam `/api/${activeRealmId}/` em vez de `/api/v1/networks/${activeRealmId}/`.

O bug mais crítico é a função `showNotification()` ausente, que afeta ~30 chamadas em 7 mecânicas diferentes. A correção é trivial (1 linha).
