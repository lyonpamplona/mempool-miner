# Auditoria Completa da Estrutura HTML

## Resumo Executivo

| Métrica | new-design.html | index.html |
|---------|-----------------|------------|
| Linhas | 1306 | 569 |
| IDs | 31 | 186 |
| Classes CSS | 45 | 88 |
| getElementById (game.js) | - | 164 únicos |

## 1. Hierarquia Principal

### Estrutura esperada (new-design.html)

```

mecha-frame

├── hud-header

├── hud-body

│   ├── stage-center

│   └── sidebar-right

└── hud-footer

```

### Verificação de elementos hierárquicos

| Elemento | new-design | index.html | Status |
|----------|------------|------------|--------|
| `mecha-frame` | ❌ | ❌ | ❌ FALTA |
| `hud-header` | ❌ | ✅ | ⚠️ |
| `hud-body` | ❌ | ✅ | ⚠️ |
| `hud-footer` | ❌ | ✅ | ⚠️ |
| `stage-center` | ✅ | ✅ | ✅ |
| `sidebar-right` | ✅ | ✅ | ✅ |

## 2. IDs: Comparação

- **IDs no new-design.html**: 31

- **IDs no index.html**: 186

- **IDs comuns**: 30

- **IDs faltando no index.html**: 1

- **IDs extras no index.html**: 156


### IDs faltando no index.html

- `tx-row-${word}`

### IDs extras no index.html (não existem no new-design)

- `achievement-toast`
- `achievement-toast-desc`
- `achievement-toast-icon`
- `achievement-toast-title`
- `achievements-filters`
- `achievements-grid`
- `achievements-modal`
- `achievements-summary`
- `boss-defeat-btn`
- `boss-defeat-modal`
- `boss-defeat-text`
- `boss-defeat-title`
- `boss-hp-bar`
- `boss-hp-text`
- `boss-hud`
- `boss-subtitle`
- `btn-achievements`
- `btn-buy-energy`
- `btn-buy-lightning`
- `btn-buy-season-premium`
- `btn-cancel-stake`
- `btn-cards`
- `btn-change-network`
- `btn-chat-toggle`
- `btn-close-achievements`
- `btn-close-crate`
- `btn-close-decoder`
- `btn-decoder-launch`
- `btn-decoder-submit`
- `btn-dismiss-event`
- `btn-dismiss-update`
- `btn-friends`
- `btn-friends-add`
- `btn-install-app`
- `btn-market`
- `btn-market-sell`
- `btn-open-crate-buy`
- `btn-open-crate-free`
- `btn-powerups-toggle`
- `btn-refresh-market`
- `btn-season`
- `btn-skills`
- `btn-sprint-mode`
- `btn-stake`
- `btn-start-session`
- `btn-update-app`
- `cards-bonus`
- `cards-common`
- `cards-epic`
- `cards-grid`
- `cards-legendary`
- `cards-loading`
- `cards-panel`
- `cards-rare`
- `cards-total`
- `chat-emoji-bar`
- `chat-input`
- `chat-messages`
- `chat-panel`
- `chat-rate-info`
- `chat-send-btn`
- `connectivity-status`
- `crate-free-count`
- `crate-icon`
- `decoder-feedback`
- `decoder-hint-letter`
- `decoder-input`
- `decoder-modal`
- `decoder-streak`
- `decoder-timer-bar`
- `decoder-timer-fill`
- `decoder-timer-text`
- `decoder-txid`
- `decoder-wins`
- `energy-bar-container`
- `friends-add-input`
- `friends-coop-bonus`
- `friends-list`
- `friends-loading`
- `friends-panel`
- `game-status`
- `game-status-footer`
- `global-event-banner`
- `global-event-countdown`
- `global-event-description`
- `global-event-icon`
- `global-event-label`
- `grid-instructions`
- `level-bar-container`
- `level-bar-fill`
- `level-bar-text`
- `level-icon`
- `level-name`
- `level-value`
- `lightning-modal`
- `lightning-text`
- `market-browse`
- `market-filter-powerup`
- `market-history`
- `market-panel`
- `market-sell`
- `market-sell-price`
- `market-sell-select`
- `missions-list`
- `missions-loading`
- `missions-panel`
- `network-select`
- `network-status`
- `next-btn`
- `pool-tag-input`
- `pools-list`
- `powerups-active`
- `powerups-bar-container`
- `pwa-update-banner`
- `pwa-update-message`
- `season-content`
- `season-id-value`
- `season-level-value`
- `season-loading`
- `season-panel`
- `season-progress-bar`
- `season-progress-fill`
- `season-progress-text`
- `season-rewards-free`
- `season-rewards-premium`
- `season-timer`
- `season-xp-value`
- `skills-content`
- `skills-header`
- `skills-level-value`
- `skills-loading`
- `skills-panel`
- `skills-points-value`
- `sprint-leaderboard-list`
- `sprint-timer-display`
- `sprint-timer-value`
- `staking-active`
- `staking-amount`
- `staking-amount-input`
- `staking-bonus`
- `staking-duration`
- `staking-form`
- `staking-history-list`
- `staking-panel`
- `staking-timer`
- `tutorial-form`
- `tutorial-modal`
- `ui-active-network`
- `ui-energy-bar`
- `ui-energy-count`
- `ui-energy-timer`
- `ui-hardware`
- `ui-miner-name`
- `ui-network-progress`
- `ui-node-status`
- `word-bank-list`

## 3. Classes CSS: Comparação

- **Classes no new-design.html**: 45

- **Classes no index.html**: 88

- **Classes comuns**: 42

- **Classes faltando no index.html**: 3

- **Classes extras no index.html**: 46


### Classes faltando no index.html

- `${badgeClass}`
- `badge-mecha`
- `tx-card-mecha`

### Classes extras no index.html

- `achievement-toast`
- `achievement-toast-content`
- `achievement-toast-desc`
- `achievement-toast-icon`
- `achievement-toast-title`
- `boss-header`
- `boss-hp-bar`
- `boss-hp-bar-container`
- `boss-hp-text`
- `boss-hud`
- `boss-icon`
- `boss-subtitle`
- `boss-title`
- `btn-powerups-toggle`
- `energy-bar-container`
- `energy-bar-fill`
- `energy-bar-track`
- `energy-count`
- `energy-label`
- `energy-timer`
- `game-instructions`
- `game-status`
- `global-event-banner`
- `global-event-banner-inner`
- `global-event-countdown`
- `global-event-description`
- `global-event-dismiss`
- `global-event-icon`
- `global-event-info`
- `global-event-label`
- `global-event-timer`
- `level-bar-container`
- `level-bar-fill`
- `level-bar-text`
- `level-bar-track`
- `level-icon`
- `level-info`
- `level-name`
- `level-value`
- `powerups-active`
- `powerups-bar-container`
- `powerups-header`
- `powerups-label`
- `season-progress-bar`
- `season-progress-fill`
- `season-progress-text`

## 4. Abas (Tabs)

| Aba | new-design | index.html | Status |
|-----|------------|------------|--------|
| `tab-tx` | ✅ | ✅ | ✅ |
| `tab-shop` | ✅ | ✅ | ✅ |
| `tab-rank` | ✅ | ✅ | ✅ |
| `tab-info` | ✅ | ✅ | ✅ |

## 5. Modais

| Modal | new-design | index.html | Status |
|-------|------------|------------|--------|
| `auth-modal` | ✅ | ✅ | ✅ |
| `result-modal` | ✅ | ✅ | ✅ |

### Modais extras no index.html

- `achievements-modal`
- `boss-defeat-modal`
- `decoder-modal`
- `lightning-modal`
- `tutorial-modal`

## 6. IDs do game.js (getElementById)

- **Total de chamadas getElementById**: 227

- **IDs únicos**: 164

- **IDs presentes no index.html**: 164

- **IDs faltando no index.html**: 0

- **IDs no game.js mas NÃO no new-design**: 141

- **IDs no game.js que ESTÃO no new-design**: 23


✅ **Todos os 164 IDs do game.js estão presentes no index.html**


### IDs no game.js mas NÃO no new-design (funcionalidades novas)

- `achievement-toast`
- `achievement-toast-desc`
- `achievement-toast-icon`
- `achievement-toast-title`
- `achievements-filters`
- `achievements-grid`
- `achievements-modal`
- `achievements-summary`
- `boss-defeat-btn`
- `boss-defeat-modal`
- `boss-defeat-text`
- `boss-defeat-title`
- `boss-hp-bar`
- `boss-hp-text`
- `boss-hud`
- `btn-achievements`
- `btn-buy-energy`
- `btn-buy-season-premium`
- `btn-cancel-stake`
- `btn-cards`
- `btn-change-network`
- `btn-chat-toggle`
- `btn-close-achievements`
- `btn-close-crate`
- `btn-close-decoder`
- `btn-decoder-launch`
- `btn-decoder-submit`
- `btn-dismiss-event`
- `btn-dismiss-update`
- `btn-friends`
- `btn-friends-add`
- `btn-install-app`
- `btn-market`
- `btn-market-sell`
- `btn-open-crate-buy`
- `btn-open-crate-free`
- `btn-powerups-toggle`
- `btn-refresh-market`
- `btn-season`
- `btn-skills`
- `btn-sprint-mode`
- `btn-stake`
- `btn-start-session`
- `btn-update-app`
- `cards-bonus`
- `cards-common`
- `cards-epic`
- `cards-grid`
- `cards-legendary`
- `cards-loading`
- `cards-panel`
- `cards-rare`
- `cards-total`
- `chat-emoji-bar`
- `chat-input`
- `chat-messages`
- `chat-panel`
- `chat-rate-info`
- `chat-send-btn`
- `connectivity-status`
- `crate-free-count`
- `crate-icon`
- `decoder-feedback`
- `decoder-hint-letter`
- `decoder-input`
- `decoder-modal`
- `decoder-streak`
- `decoder-timer-bar`
- `decoder-timer-text`
- `decoder-txid`
- `decoder-wins`
- `friends-add-input`
- `friends-coop-bonus`
- `friends-list`
- `friends-loading`
- `friends-panel`
- `game-status`
- `global-event-banner`
- `global-event-countdown`
- `global-event-description`
- `global-event-icon`
- `global-event-label`
- `level-bar-container`
- `level-bar-fill`
- `level-bar-text`
- `level-icon`
- `level-name`
- `level-value`
- `lightning-modal`
- `lightning-text`
- `market-browse`
- `market-filter-powerup`
- `market-history`
- `market-panel`
- `market-sell`
- `market-sell-price`
- `market-sell-select`
- `missions-list`
- `missions-loading`
- `missions-panel`
- `network-select`
- `network-status`
- `next-btn`
- `pool-tag-input`
- `powerups-bar-container`
- `pwa-update-banner`
- `season-content`
- `season-id-value`
- `season-level-value`
- `season-loading`
- `season-panel`
- `season-progress-bar`
- `season-progress-fill`
- `season-progress-text`
- `season-rewards-free`
- `season-rewards-premium`
- `season-timer`
- `season-xp-value`
- `skills-content`
- `skills-header`
- `skills-level-value`
- `skills-loading`
- `skills-panel`
- `skills-points-value`
- `sprint-leaderboard-list`
- `sprint-timer-display`
- `sprint-timer-value`
- `staking-active`
- `staking-amount`
- `staking-amount-input`
- `staking-bonus`
- `staking-duration`
- `staking-form`
- `staking-history-list`
- `staking-panel`
- `staking-timer`
- `ui-active-network`
- `ui-energy-bar`
- `ui-energy-count`
- `ui-energy-timer`
- `ui-node-status`

## 7. Conclusão

### Resumo de conformidade

⚠️ - 1 ID(s) do new-design faltam no index.html

⚠️ - 3 classe(s) CSS do new-design faltam no index.html


### Observações

- O index.html tem **156 IDs extras** e **46 classes extras** em relação ao new-design.html, correspondendo a funcionalidades adicionais implementadas no game.js (achievements, boss battles, decoder, market, staking, seasons, skills, chat, friends, cards, energy, global events, PWA, etc.)

- O index.html é **569 linhas** vs **1306 linhas** do new-design.html

- O new-design.html serve como base de referência visual; o index.html é a versão funcional completa
