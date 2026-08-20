# AUDITORIA COMPLETA DO CSS — Conflitos entre style.css e pixel.css

> **Data**: 19 de Agosto de 2026
> **Objetivo**: Identificar TODOS os conflitos entre style.css (456 classes) e pixel.css (361 classes)
> **Referencia**: new-design.html (56 classes, CSS inline de 18KB)

## 1. RESUMO EXECUTIVO

| Metrica | Valor |
|---------|-------|
| Classes no novo design (new-design.html) | 56 |
| Classes no style.css | 456 |
| Classes no pixel.css | 361 |
| Classes sobrepostas (style.css e pixel.css) | 302 |
| Classes apenas no style.css | 154 |
| Classes apenas no pixel.css | 59 |
| Aliases CORRETOS no pixel.css | 6 |
| Aliases ERRADOS no pixel.css | 296 |
| Variaveis CSS no novo design | 19 |
| Variaveis CSS no style.css | 18 |
| Variaveis CSS no pixel.css | 21 |

## 2. DIAGNOSTICO PRINCIPAL

O problema central e que o **pixel.css contem 296 aliases errados** que copiam propriedades do style.css antigo
em vez de implementar o novo design Mecha Sci-Fi Industrial. O style.css e carregado ANTES do pixel.css,
mas como ambos definem as mesmas classes, o pixel.css deveria sobrescrever com o novo design — porem na maioria
dos casos, o pixel.css apenas replica o style.css antigo com pequenas variacoes.

### Causa raiz:
1. O pixel.css foi gerado como um arquivo de 'aliases' que mapeia classes do HTML/game.js para o tema Mecha
2. Porem, a maioria desses aliases copia as propriedades do style.css antigo (tema glass/dark) em vez do novo design
3. O style.css continua sendo carregado e suas 456 classes conflitam com as 361 do pixel.css
4. 302 classes sao sobrepostas, e 296 delas tem aliases errados

## 3. VARIÁVEIS CSS CONFLITANTES

### 3.1 Variaveis NOVAS (apenas no novo design, ausentes do style.css)

**18 variaveis que o style.css nao tem:**

| Variavel | Valor no novo design |
|----------|---------------------|
| `--bg-void` | `#0e1117` |
| `--border-dim` | `#30363d` |
| `--border-glow` | `rgba(0, 255, 136, 0.4)` |
| `--border-hi` | `#484f58` |
| `--f-data` | `'VT323', monospace` |
| `--f-pixel` | `'Press Start 2P', monospace` |
| `--f-tech` | `'JetBrains Mono', monospace` |
| `--hull-dark` | `#161b22` |
| `--hull-panel` | `#1f242d` |
| `--hull-surface` | `#272d38` |
| `--neon-amber` | `#00f0ff` |
| `--neon-cyan` | `#00ff88` |
| `--neon-gold` | `#ffcc00` |
| `--neon-green` | `#00ff88` |
| `--neon-magenta` | `#f000ff` |
| `--neon-red` | `#ff3355` |
| `--text-dark` | `#484f58` |
| `--text-dim` | `#8b949e` |

### 3.2 Variaveis VELHAS (apenas no style.css, ausentes do novo design)

**17 variaveis que o novo design nao usa mais:**

| Variavel | Valor no style.css |
|----------|-------------------|
| `--bg-dark` | `#020617` |
| `--btc-orange` | `#0ea5e9` |
| `--cell-size` | `20px` |
| `--energy-yellow` | `#facc15` |
| `--error-red` | `#ef4444` |
| `--font-mono` | `'JetBrains Mono', ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace` |
| `--glass-bg` | `rgba(15, 15, 18, 0.82)` |
| `--glass-border` | `rgba(255, 255, 255, 0.1)` |
| `--golden-hash` | `#eab308` |
| `--grid-gap` | `2px` |
| `--high-fee` | `#a855f7` |
| `--hint-yellow` | `#fde047` |
| `--lightning-blue` | `#0ea5e9` |
| `--page-max` | `1400px` |
| `--success-green` | `#22c55e` |
| `--text-muted` | `#94a3b8` |
| `--warning-orange` | `#f97316` |

### 3.3 Variaveis com valores diferentes (novo design vs style.css)

| `--text-main` | novo: `#f0f6fc` | style.css: `#e2e8f0` |

Total de variaveis com valores diferentes: 1

### 3.4 Variaveis no pixel.css vs novo design

- Coincidem com novo design: 19
- Diferem do novo design: 0

## 4. CLASSES DO NOVO DESIGN — STATUS DE IMPLEMENTACAO

### 4.1 Classes do novo design presentes no pixel.css (56 de 56)

- `active`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `amber`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `badge-gold`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `badge-high`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `badge-mecha`: OK (100% match, 4 props ND vs 4 props pixel.css)
- `badge-std`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `btn-action-small`: OK (100% match, 10 props ND vs 10 props pixel.css)
- `btn-index`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `cell`: OK (100% match, 14 props ND vs 14 props pixel.css)
- `cross-line`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `cyan`: OK (100% match, 1 props ND vs 1 props pixel.css)
- `float-pts`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `found`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `green`: OK (100% match, 1 props ND vs 1 props pixel.css)
- `grid-hull`: OK (100% match, 7 props ND vs 7 props pixel.css)
- `grid-overlay`: OK (100% match, 9 props ND vs 9 props pixel.css)
- `hidden`: OK (100% match, 1 props ND vs 1 props pixel.css)
- `hint`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `hud-body`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `hud-footer`: OK (100% match, 11 props ND vs 11 props pixel.css)
- `hud-header`: OK (100% match, 9 props ND vs 9 props pixel.css)
- `hud-metrics`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `hud-sys-tag`: OK (100% match, 7 props ND vs 7 props pixel.css)
- `hud-title-zone`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `input-mecha`: OK (100% match, 11 props ND vs 11 props pixel.css)
- `left`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `lightning-active`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `mecha-btn`: OK (100% match, 22 props ND vs 22 props pixel.css)
- `mecha-frame`: OK (100% match, 10 props ND vs 10 props pixel.css)
- `mecha-nav-group`: OK (100% match, 4 props ND vs 4 props pixel.css)
- `metric-lbl`: OK (100% match, 4 props ND vs 4 props pixel.css)
- `metric-unit`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `metric-val`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `mev-found`: OK (100% match, 4 props ND vs 4 props pixel.css)
- `modal-mecha-box`: OK (100% match, 10 props ND vs 10 props pixel.css)
- `modal-wrap`: OK (100% match, 9 props ND vs 9 props pixel.css)
- `panel-code-tag`: OK (100% match, 10 props ND vs 10 props pixel.css)
- `race-bar`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `race-box`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `race-chute`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `race-header`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `rail-notch`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `rbf`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `right`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `sel`: OK (100% match, 4 props ND vs 4 props pixel.css)
- `shop-card-mecha`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `shop-row`: OK (100% match, 3 props ND vs 3 props pixel.css)
- `side-rail`: OK (100% match, 14 props ND vs 14 props pixel.css)
- `sidebar-right`: OK (100% match, 7 props ND vs 7 props pixel.css)
- `spinner-mecha`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `stage-center`: OK (100% match, 17 props ND vs 17 props pixel.css)
- `status-slot`: OK (100% match, 2 props ND vs 2 props pixel.css)
- `svg-layer`: OK (100% match, 6 props ND vs 6 props pixel.css)
- `tab-pane`: OK (100% match, 5 props ND vs 5 props pixel.css)
- `tx-card-mecha`: OK (100% match, 10 props ND vs 10 props pixel.css)
- `word-grid`: OK (100% match, 5 props ND vs 5 props pixel.css)

### 4.2 Classes do novo design FALTANDO no pixel.css

Todas as 56 classes do novo design estao presentes no pixel.css.

## 5. LISTA COMPLETA DOS 296 ALIASES ERRADOS

Estas classes no pixel.css copiam propriedades do style.css antigo em vez do novo design:

| Classe | No novo design? | Props style.css | Props pixel.css |
|--------|----------------|-----------------|-----------------|
| `achievement-toast` | NAO | 15 | 1 |
| `achievement-toast-content` | NAO | 3 | 3 |
| `achievement-toast-desc` | NAO | 2 | 2 |
| `achievement-toast-icon` | NAO | 3 | 1 |
| `achievement-toast-title` | NAO | 3 | 3 |
| `achievements-filters` | NAO | 4 | 4 |
| `achievements-grid` | NAO | 6 | 1 |
| `achievements-modal-content` | NAO | 4 | 4 |
| `achievements-summary` | NAO | 10 | 8 |
| `app-action` | NAO | 11 | 1 |
| `app-action-primary` | NAO | 2 | 2 |
| `app-status` | NAO | 7 | 7 |
| `available` | NAO | 7 | 2 |
| `boss-active` | NAO | 1 | 1 |
| `boss-flash` | NAO | 1 | 1 |
| `boss-header` | NAO | 8 | 8 |
| `boss-hp-bar` | NAO | 6 | 5 |
| `boss-hp-bar-container` | NAO | 8 | 8 |
| `boss-hp-damage` | NAO | 1 | 1 |
| `boss-hp-text` | NAO | 10 | 10 |
| `boss-hud` | NAO | 11 | 11 |
| `boss-icon` | NAO | 2 | 2 |
| `boss-shake` | NAO | 1 | 1 |
| `boss-subtitle` | NAO | 4 | 4 |
| `boss-title` | NAO | 6 | 6 |
| `btn` | NAO | 15 | 3 |
| `btn-crate-buy` | NAO | 6 | 3 |
| `btn-crate-free` | NAO | 6 | 3 |
| `btn-decoder` | NAO | 13 | 12 |
| `btn-decoder-launch` | NAO | 18 | 1 |
| `btn-energy` | NAO | 4 | 2 |
| `btn-friends-add` | NAO | 12 | 1 |
| `btn-hardware` | NAO | 9 | 9 |
| `btn-lightning` | NAO | 2 | 2 |
| `btn-market-refresh` | NAO | 7 | 7 |
| `btn-market-sell` | NAO | 9 | 9 |
| `btn-network-change` | NAO | 10 | 10 |
| `btn-powerups-toggle` | NAO | 8 | 8 |
| `btn-premium` | NAO | 12 | 9 |
| `btn-pvp-challenge` | NAO | 9 | 9 |
| `btn-pvp-close` | NAO | 8 | 8 |
| `btn-sprint-toggle` | NAO | 13 | 2 |
| `btn-stake` | NAO | 2 | 2 |
| `btn-stake-cancel` | NAO | 4 | 4 |
| `btn-store` | NAO | 11 | 10 |
| `card-filter` | NAO | 12 | 11 |
| `cards-bonus` | NAO | 5 | 5 |
| `cards-filters` | NAO | 5 | 5 |
| `cards-grid` | NAO | 6 | 6 |
| `cards-panel` | NAO | 1 | 1 |
| `cards-stat-item` | NAO | 7 | 7 |
| `cards-stat-label` | NAO | 1 | 1 |
| `cards-stat-value` | NAO | 2 | 2 |
| `cards-stats` | NAO | 5 | 5 |
| `chat-emoji-bar` | NAO | 4 | 4 |
| `chat-emoji-btn` | NAO | 11 | 3 |
| `chat-input` | NAO | 12 | 10 |
| `chat-input-area` | NAO | 4 | 4 |
| `chat-input-row` | NAO | 2 | 2 |
| `chat-messages` | NAO | 8 | 1 |
| `chat-panel` | NAO | 3 | 1 |
| `chat-rate-info` | NAO | 4 | 4 |
| `chat-send-btn` | NAO | 12 | 11 |
| `claimed` | NAO | 3 | 2 |
| `combo-value` | NAO | 1 | 1 |
| `completed` | NAO | 2 | 2 |
| `connectivity-pill` | NAO | 15 | 1 |
| `crate-box` | NAO | 2 | 2 |
| `crate-buttons` | NAO | 3 | 1 |
| `crate-counts` | NAO | 4 | 4 |
| `crate-divider` | NAO | 2 | 2 |
| `crate-free` | NAO | 3 | 3 |
| `crate-icon` | NAO | 3 | 1 |
| `crate-item` | NAO | 1 | 1 |
| `crate-item-desc` | NAO | 2 | 2 |
| `crate-item-icon` | NAO | 1 | 1 |
| `crate-item-name` | NAO | 3 | 3 |
| `crate-item-rarity` | NAO | 6 | 6 |
| `crate-item-reveal` | NAO | 5 | 5 |
| `crate-modal-content` | NAO | 8 | 1 |
| `crate-opening-animation` | NAO | 4 | 4 |
| `crate-particles` | NAO | 5 | 5 |
| `crate-price` | NAO | 2 | 2 |
| `crate-result` | NAO | 2 | 2 |
| `dashboard` | NAO | 8 | 1 |
| `decoder-content` | NAO | 7 | 4 |
| `decoder-feedback` | NAO | 10 | 1 |
| `decoder-hint` | NAO | 7 | 7 |
| `decoder-hint-label` | NAO | 5 | 5 |
| `decoder-hint-value` | NAO | 4 | 4 |
| `decoder-input` | NAO | 13 | 11 |
| `decoder-input-row` | NAO | 3 | 3 |
| `decoder-stat` | NAO | 3 | 3 |
| `decoder-stats` | NAO | 5 | 5 |
| `decoder-timer-bar` | NAO | 5 | 4 |
| `decoder-timer-container` | NAO | 6 | 6 |
| `decoder-timer-text` | NAO | 10 | 10 |
| `decoder-txid` | NAO | 12 | 12 |
| `energy-bar-container` | NAO | 5 | 5 |
| `energy-bar-fill` | NAO | 6 | 5 |
| `energy-bar-track` | NAO | 5 | 5 |
| `energy-count` | NAO | 6 | 6 |
| `energy-item` | NAO | 3 | 2 |
| `energy-label` | NAO | 6 | 6 |
| `energy-timer` | NAO | 5 | 5 |
| `friends-add-form` | NAO | 2 | 1 |
| `friends-add-input` | NAO | 7 | 7 |
| `friends-add-section` | NAO | 2 | 2 |
| `friends-coop-bonus` | NAO | 9 | 9 |
| `friends-list` | NAO | 6 | 6 |
| `friends-panel` | NAO | 1 | 1 |
| `game-area` | NAO | 6 | 4 |
| `game-instructions` | NAO | 4 | 3 |
| `game-status` | NAO | 5 | 1 |
| `glass-panel` | NAO | 6 | 6 |
| `global-event-banner` | NAO | 14 | 7 |
| `global-event-banner-inner` | NAO | 7 | 2 |
| `global-event-countdown` | NAO | 9 | 2 |
| `global-event-description` | NAO | 3 | 1 |
| `global-event-dismiss` | NAO | 8 | 8 |
| `global-event-icon` | NAO | 3 | 1 |
| `global-event-info` | NAO | 4 | 4 |
| `global-event-label` | NAO | 5 | 1 |
| `global-event-timer` | NAO | 1 | 1 |
| `grid-wrapper` | NAO | 10 | 2 |
| `halving` | NAO | 1 | 1 |
| `halving-flash` | NAO | 1 | 1 |
| `hidden` | SIM | 4 | 1 |
| `hint-glow` | NAO | 4 | 4 |
| `leaderboard-list` | NAO | 3 | 3 |
| `level-bar-container` | NAO | 3 | 3 |
| `level-bar-fill` | NAO | 4 | 4 |
| `level-bar-text` | NAO | 9 | 9 |
| `level-bar-track` | NAO | 6 | 6 |
| `level-icon` | NAO | 1 | 1 |
| `level-info` | NAO | 4 | 1 |
| `level-name` | NAO | 4 | 1 |
| `level-value` | NAO | 4 | 1 |
| `leveled-up` | NAO | 2 | 2 |
| `lightning-item` | NAO | 3 | 2 |
| `lightning-theme` | NAO | 7 | 3 |
| `loader-spinner` | NAO | 7 | 7 |
| `loader-text` | NAO | 4 | 3 |
| `loading-state` | NAO | 6 | 6 |
| `low` | NAO | 4 | 1 |
| `main-layout` | NAO | 7 | 3 |
| `market-filters` | NAO | 3 | 3 |
| `market-inventory` | NAO | 3 | 3 |
| `market-listings` | NAO | 3 | 3 |
| `market-panel` | NAO | 1 | 1 |
| `market-sales-history` | NAO | 3 | 3 |
| `market-section` | NAO | 2 | 1 |
| `market-sell-form` | NAO | 4 | 4 |
| `market-sell-input` | NAO | 6 | 6 |
| `market-sell-select` | NAO | 6 | 6 |
| `market-tab-btn` | NAO | 11 | 10 |
| `market-tabs` | NAO | 4 | 4 |
| `miner-input` | NAO | 12 | 6 |
| `miner-name` | NAO | 1 | 1 |
| `mining-stats` | NAO | 5 | 1 |
| `missions-list` | NAO | 3 | 3 |
| `missions-panel` | NAO | 2 | 2 |
| `mobile-nav` | NAO | 16 | 1 |
| `mobile-nav-btn` | NAO | 12 | 12 |
| `modal-content` | NAO | 8 | 1 |
| `modal-overlay` | NAO | 15 | 1 |
| `modal-text` | NAO | 4 | 4 |
| `modal-title` | NAO | 6 | 3 |
| `mt-auto` | NAO | 1 | 1 |
| `network-badge` | NAO | 1 | 1 |
| `network-label` | NAO | 7 | 2 |
| `network-select` | NAO | 14 | 11 |
| `network-status` | NAO | 4 | 4 |
| `node-status` | NAO | 3 | 3 |
| `offline` | NAO | 3 | 2 |
| `panel-header` | NAO | 8 | 8 |
| `pool-tag-input` | NAO | 14 | 4 |
| `pool-tag-label` | NAO | 7 | 7 |
| `powerups-active` | NAO | 3 | 3 |
| `powerups-bar-container` | NAO | 6 | 6 |
| `powerups-header` | NAO | 3 | 3 |
| `powerups-label` | NAO | 3 | 3 |
| `pvp-actions` | NAO | 1 | 1 |
| `pvp-challenge-form` | NAO | 9 | 3 |
| `pvp-challenged-card` | NAO | 1 | 1 |
| `pvp-challenger-card` | NAO | 1 | 1 |
| `pvp-countdown-content` | NAO | 4 | 4 |
| `pvp-countdown-number` | NAO | 5 | 5 |
| `pvp-countdown-words` | NAO | 2 | 2 |
| `pvp-match-info` | NAO | 1 | 1 |
| `pvp-panel` | NAO | 1 | 1 |
| `pvp-player-card` | NAO | 8 | 8 |
| `pvp-player-found` | NAO | 2 | 2 |
| `pvp-player-label` | NAO | 4 | 4 |
| `pvp-player-name` | NAO | 4 | 4 |
| `pvp-player-score` | NAO | 2 | 2 |
| `pvp-progress-bar-container` | NAO | 5 | 5 |
| `pvp-progress-container` | NAO | 1 | 1 |
| `pvp-progress-fill` | NAO | 2 | 2 |
| `pvp-progress-fill-challenged` | NAO | 1 | 1 |
| `pvp-progress-fill-challenger` | NAO | 1 | 1 |
| `pvp-progress-label` | NAO | 3 | 3 |
| `pvp-result-content` | NAO | 4 | 4 |
| `pvp-result-icon` | NAO | 3 | 3 |
| `pvp-result-scores` | NAO | 3 | 3 |
| `pvp-result-text` | NAO | 2 | 2 |
| `pvp-result-title` | NAO | 4 | 4 |
| `pvp-status` | NAO | 1 | 1 |
| `pvp-status-text` | NAO | 2 | 2 |
| `pvp-timer-bar` | NAO | 4 | 4 |
| `pvp-timer-bar-container` | NAO | 6 | 6 |
| `pvp-timer-text` | NAO | 5 | 5 |
| `pvp-vs-badge` | NAO | 4 | 4 |
| `race-bar-network` | NAO | 7 | 7 |
| `race-track` | NAO | 9 | 6 |
| `revealed` | NAO | 1 | 1 |
| `reward` | NAO | 3 | 1 |
| `season-content` | NAO | 1 | 1 |
| `season-header` | NAO | 2 | 2 |
| `season-info` | NAO | 4 | 4 |
| `season-label` | NAO | 1 | 1 |
| `season-panel` | NAO | 1 | 1 |
| `season-progress` | NAO | 1 | 1 |
| `season-progress-bar` | NAO | 6 | 6 |
| `season-progress-fill` | NAO | 4 | 4 |
| `season-progress-text` | NAO | 5 | 5 |
| `season-rewards-list` | NAO | 3 | 3 |
| `season-tab` | NAO | 10 | 8 |
| `season-tabs` | NAO | 3 | 3 |
| `season-timer` | NAO | 4 | 4 |
| `season-value` | NAO | 2 | 2 |
| `selected` | NAO | 7 | 4 |
| `session-submit` | NAO | 2 | 2 |
| `side-panel` | NAO | 3 | 3 |
| `skills-branches` | NAO | 5 | 5 |
| `skills-content` | NAO | 1 | 1 |
| `skills-header` | NAO | 7 | 7 |
| `skills-level-info` | NAO | 4 | 4 |
| `skills-level-label` | NAO | 1 | 1 |
| `skills-level-value` | NAO | 3 | 3 |
| `skills-panel` | NAO | 2 | 2 |
| `skills-points-info` | NAO | 4 | 3 |
| `skills-points-label` | NAO | 1 | 3 |
| `skills-points-value` | NAO | 3 | 3 |
| `skip-link` | NAO | 10 | 10 |
| `slashing-flash` | NAO | 1 | 1 |
| `sprint-leaderboard-list` | NAO | 4 | 3 |
| `sprint-panel` | NAO | 1 | 3 |
| `sprint-timer` | NAO | 6 | 4 |
| `sprint-timer-container` | NAO | 8 | 2 |
| `staking-active` | NAO | 7 | 7 |
| `staking-amount-input` | NAO | 3 | 3 |
| `staking-bonus` | NAO | 1 | 1 |
| `staking-countdown` | NAO | 8 | 8 |
| `staking-countdown-label` | NAO | 2 | 2 |
| `staking-countdown-value` | NAO | 4 | 1 |
| `staking-desc` | NAO | 3 | 3 |
| `staking-duration-bonus` | NAO | 2 | 2 |
| `staking-duration-btn` | NAO | 14 | 13 |
| `staking-duration-value` | NAO | 2 | 2 |
| `staking-durations` | NAO | 3 | 3 |
| `staking-form` | NAO | 3 | 3 |
| `staking-history` | NAO | 6 | 6 |
| `staking-history-list` | NAO | 5 | 5 |
| `staking-history-title` | NAO | 5 | 5 |
| `staking-info-label` | NAO | 2 | 2 |
| `staking-info-row` | NAO | 5 | 5 |
| `staking-info-value` | NAO | 3 | 3 |
| `staking-input` | NAO | 11 | 10 |
| `staking-label` | NAO | 4 | 4 |
| `staking-panel` | NAO | 3 | 3 |
| `staking-status-bar` | NAO | 3 | 3 |
| `staking-status-label` | NAO | 4 | 4 |
| `staking-status-value` | NAO | 3 | 3 |
| `staking-warning` | NAO | 3 | 3 |
| `stat-box` | NAO | 4 | 4 |
| `stat-val` | NAO | 4 | 4 |
| `store-desc` | NAO | 3 | 3 |
| `store-info` | NAO | 3 | 3 |
| `store-item` | NAO | 8 | 8 |
| `store-panel` | NAO | 3 | 3 |
| `store-title` | NAO | 3 | 1 |
| `svg-lines` | NAO | 6 | 6 |
| `unlocked` | NAO | 4 | 1 |
| `update-actions` | NAO | 3 | 3 |
| `update-banner` | NAO | 11 | 1 |
| `urgent` | NAO | 2 | 1 |
| `visible` | NAO | 2 | 2 |
| `visually-hidden` | NAO | 9 | 9 |
| `wallet-balance` | NAO | 5 | 5 |
| `wallet-info` | NAO | 4 | 3 |
| `wallet-label` | NAO | 5 | 5 |
| `warning` | NAO | 2 | 2 |
| `weekly` | NAO | 4 | 3 |
| `word-bank` | NAO | 3 | 1 |
| `word-bank-list` | NAO | 3 | 1 |

## 6. LISTA DOS 6 ALIASES CORRETOS

Estas classes no pixel.css seguem corretamente o novo design:

- `active`
- `cell`
- `cross-line`
- `found`
- `grid-overlay`
- `word-grid`

## 7. RECOMENDACOES DE CORRECAO

### Opcao A: Substituir style.css pelo novo design (RECOMENDADO)

1. **Remover o style.css** como arquivo principal de estilos
2. **Criar um novo style.css** contendo:
   - As 56 classes do novo design (new-design.html) com propriedades completas
   - As variaveis CSS do novo design (:root)
   - As classes extras do game.js que precisam de estilos (boss battles, achievements, chat, etc.)
   - Estilizar todas as classes extras com o tema Mecha Sci-Fi Industrial
3. **Remover o pixel.css** (ou mante-lo apenas para aliases que realmente precisem sobrescrever)
4. **Atualizar o HTML** para carregar apenas o novo style.css

### Opcao B: Corrigir o pixel.css (MENOS INVASIVO)

1. **Manter o style.css** mas remover todas as classes que conflitam com o novo design
2. **Reescrever o pixel.css** para que:
   - As 56 classes do novo design tenham as propriedades CORRETAS (do new-design.html)
   - Os 296 aliases errados sejam corrigidos para seguir o tema Mecha
   - As variaveis CSS do :root sejam as do novo design
3. **Manter a ordem de carregamento**: style.css primeiro, pixel.css depois

### Opcao C: Unificar em um unico arquivo (MAIS LIMPO)

1. **Fundir style.css + pixel.css** em um unico arquivo CSS
2. **Priorizar o novo design** para todas as 56 classes
3. **Estilizar todas as classes extras** (boss, achievements, chat, PVP, etc.) com o tema Mecha
4. **Remover duplicacoes** e conflitos
5. **Resultado**: um unico arquivo CSS limpo, sem conflitos de especificidade

## 8. DETALHAMENTO DAS 302 CLASSES SOBREPOSTAS

Para cada classe: propriedades do style.css vs pixel.css vs novo design

## Detalhamento das 302 Classes Sobrepostas

Para cada classe: propriedades do style.css vs pixel.css vs novo design

### `achievement-toast` [NAO-NOVO-DESIGN]
- style.css: 15 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (14): backdrop-filter, background, border, border-radius, box-shadow, left, max-width, opacity, padding, pointer-events...

### `achievement-toast-content` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `achievement-toast-desc` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `achievement-toast-icon` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `animation`: style.css=`achievementBounce 0.6s ease` vs pixel.css=`none`
- **Apenas no style.css** (2): flex-shrink, font-size

### `achievement-toast-title` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `achievements-filters` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `achievements-grid` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `grid-template-columns`: style.css=`repeat(auto-fill, minmax(160px, 1fr))` vs pixel.css=`repeat(auto-fill, minmax(140px, 1fr))`
- **Apenas no style.css** (5): display, gap, max-height, overflow-y, padding

### `achievements-modal-content` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `achievements-summary` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.03)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`
  - `font-size`: style.css=`11px` vs pixel.css=`12px`
- **Apenas no style.css** (2): color, font-weight

### `active` [NOVO-DESIGN]
- style.css: 8 props | pixel.css: 5 props | novo design: 5 props
- pixel.css alinhamento: 100% novo-design / 0% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`linear-gradient(135deg, #22c55e, #16a34a)` vs pixel.css=`#e6edf3`
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`#fff`
  - `color`: style.css=`#fff` vs pixel.css=`#57606a`
- **Apenas no style.css** (5): font-weight, opacity, pointer-events, transform, visibility
- **Apenas no pixel.css** (2): box-shadow, display

### `app-action` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
- **Apenas no style.css** (10): align-items, background, border-radius, color, cursor, display, font-size, justify-content, min-height, padding

### `app-action-primary` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `app-status` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `available` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (5): animation, background, box-shadow, color, transform

### `boss-active` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `boss-flash` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `boss-header` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(239, 68, 68, 0.2)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(239, 68, 68, 0.5)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`999px` vs pixel.css=`0`

### `boss-hp-bar` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`linear-gradient(90deg, var(--error-red), #ff6b6b)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`7px` vs pixel.css=`0`
- **Apenas no style.css** (1): animation

### `boss-hp-bar-container` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(0, 0, 0, 0.6)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(239, 68, 68, 0.4)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`7px` vs pixel.css=`0`

### `boss-hp-damage` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `boss-hp-text` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`#fff` vs pixel.css=`var(--text-main)`

### `boss-hud` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 11 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `display`: style.css=`none` vs pixel.css=`flex`

### `boss-icon` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `boss-shake` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `boss-subtitle` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--golden-hash)` vs pixel.css=`var(--text-main)`

### `boss-title` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`

### `btn` [NAO-NOVO-DESIGN]
- style.css: 15 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(14, 165, 233, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`var(--warning-orange)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--warning-orange)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (12): animation, border, border-radius, cursor, font-size, font-weight, letter-spacing, min-height, opacity, padding...

### `btn-crate-buy` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`#f59e0b` vs pixel.css=`var(--hull-surface)`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): box-shadow, cursor, opacity

### `btn-crate-free` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`var(--text-muted)` vs pixel.css=`var(--hull-surface)`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): box-shadow, cursor, opacity

### `btn-decoder` [NAO-NOVO-DESIGN]
- style.css: 13 props | pixel.css: 12 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (5):
  - `background`: style.css=`rgba(247, 147, 26, 0.15)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--btc-orange)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`
  - `cursor`: style.css=`not-allowed` vs pixel.css=`pointer`
- **Apenas no style.css** (1): opacity

### `btn-decoder-launch` [NAO-NOVO-DESIGN]
- style.css: 18 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `animation`: style.css=`decoderLaunchPulse 2s ease-in-out infinite` vs pixel.css=`none`
- **Apenas no style.css** (17): background, border, border-radius, bottom, box-shadow, color, cursor, display, font-size, font-weight...

### `btn-energy` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `border-color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): cursor, opacity

### `btn-friends-add` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `padding`: style.css=`8px 16px` vs pixel.css=`10px`
- **Apenas no style.css** (11): background, border, border-radius, box-shadow, color, cursor, font-size, font-weight, opacity, transform...

### `btn-hardware` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--warning-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`

### `btn-lightning` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `border-color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`

### `btn-market-refresh` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--btc-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`

### `btn-market-sell` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--warning-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`

### `btn-network-change` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`transparent` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`0` vs pixel.css=`1px solid var(--border-hi)`
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `btn-powerups-toggle` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `btn-premium` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (5):
  - `background`: style.css=`linear-gradient(135deg, var(--btc-orange), #ffd700)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`
  - `cursor`: style.css=`not-allowed` vs pixel.css=`pointer`
- **Apenas no style.css** (3): box-shadow, opacity, transform

### `btn-pvp-challenge` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--warning-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`

### `btn-pvp-close` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `btn-sprint-toggle` [NAO-NOVO-DESIGN]
- style.css: 13 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `font-size`: style.css=`14px` vs pixel.css=`12px`
  - `padding`: style.css=`8px 16px` vs pixel.css=`6px 12px`
- **Apenas no style.css** (11): background, border, border-radius, box-shadow, color, cursor, font-weight, letter-spacing, text-transform, transform...

### `btn-stake` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `btn-stake-cancel` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--error-red)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`#fff` vs pixel.css=`var(--text-main)`

### `btn-store` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`transparent` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--text-muted)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `cursor`: style.css=`not-allowed` vs pixel.css=`pointer`
- **Apenas no style.css** (1): opacity

### `card-filter` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 11 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`#f59e0b` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#fff` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): border-color

### `cards-bonus` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `cards-filters` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `cards-grid` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `cards-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `cards-stat-item` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `cards-stat-label` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `cards-stat-value` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `cards-stats` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `cell` [NOVO-DESIGN]
- style.css: 23 props | pixel.css: 14 props | novo design: 14 props
- pixel.css alinhamento: 100% novo-design / 21% style.css
- **Propriedades CONFLITANTES** (10):
  - `animation`: style.css=`pulseHint 1s infinite alternate` vs pixel.css=`pulseHint 0.8s infinite alternate`
  - `background`: style.css=`rgba(14, 165, 233, 0.22)` vs pixel.css=`rgba(255, 51, 85, 0.25)`
  - `border`: style.css=`1px solid rgba(255, 255, 255, 0.04)` vs pixel.css=`1px solid rgba(255,255,255,0.03)`
  - `border-color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--neon-gold)`
  - `box-shadow`: style.css=`0 0 12px rgba(14, 165, 233, 0.3)` vs pixel.css=`0 0 12px rgba(255,51,85,0.5)`
  - `color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--neon-gold)`
  - `cursor`: style.css=`crosshair` vs pixel.css=`pointer`
  - `font-size`: style.css=`clamp(9px, calc(var(--cell-size) * 0.48), 18px)` vs pixel.css=`clamp(14px, 3.2vh, 30px)`
  - `font-weight`: style.css=`600` vs pixel.css=`700`
  - `transition`: style.css=`background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.15s ease` vs pixel.css=`background 0.1s, color 0.1s, transform 0.05s`
- **Apenas no style.css** (10): border-radius, contain, height, line-height, outline, outline-offset, position, transform, width, z-index
- **Apenas no pixel.css** (1): font-family

### `chat-emoji-bar` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `chat-emoji-btn` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `font-size`: style.css=`14px` vs pixel.css=`12px`
  - `min-height`: style.css=`30px` vs pixel.css=`28px`
  - `min-width`: style.css=`30px` vs pixel.css=`28px`
- **Apenas no style.css** (8): background, border, border-color, border-radius, color, cursor, padding, transition

### `chat-input` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`rgba(255, 255, 255, 0.05)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): border-color, opacity

### `chat-input-area` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `chat-input-row` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `chat-messages` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `max-height`: style.css=`400px` vs pixel.css=`250px`
- **Apenas no style.css** (7): display, flex, flex-direction, gap, min-height, overflow-y, padding

### `chat-panel` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `max-height`: style.css=`70vh` vs pixel.css=`650px`
- **Apenas no style.css** (2): display, flex-direction

### `chat-rate-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`

### `chat-send-btn` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 11 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (5):
  - `background`: style.css=`var(--btc-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--btc-orange)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--bg-dark)` vs pixel.css=`var(--text-main)`
  - `cursor`: style.css=`not-allowed` vs pixel.css=`pointer`
- **Apenas no style.css** (1): opacity

### `claimed` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): background

### `combo-value` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `completed` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`var(--success-green)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`rgba(34, 197, 94, 0.4)` vs pixel.css=`var(--text-main)`

### `connectivity-pill` [NAO-NOVO-DESIGN]
- style.css: 15 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (14): align-items, background, border, border-color, border-radius, color, content, display, font-size, height...

### `crate-box` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-buttons` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (3): display, gap, margin-top
- **Apenas no pixel.css** (1): flex-direction

### `crate-counts` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-divider` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `crate-free` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `crate-icon` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`80px` vs pixel.css=`60px`
- **Apenas no style.css** (2): animation, margin-bottom

### `crate-item` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--golden-hash)` vs pixel.css=`var(--text-main)`

### `crate-item-desc` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `crate-item-icon` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-item-name` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-item-rarity` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `crate-item-reveal` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-modal-content` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `padding`: style.css=`32px` vs pixel.css=`24px`
- **Apenas no style.css** (7): animation, background, border, border-radius, max-width, text-align, width

### `crate-opening-animation` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-particles` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `crate-price` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `crate-result` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `cross-line` [NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 5 props
- pixel.css alinhamento: 100% novo-design / 20% style.css
- **Propriedades CONFLITANTES** (4):
  - `opacity`: style.css=`0.35` vs pixel.css=`0.45`
  - `stroke`: style.css=`var(--success-green)` vs pixel.css=`var(--neon-green)`
  - `stroke-width`: style.css=`18` vs pixel.css=`clamp(8px, 1.8vh, 18px)`
  - `transition`: style.css=`stroke-dashoffset 0.4s ease-out` vs pixel.css=`stroke-dashoffset 0.3s ease-out`

### `dashboard` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `grid-template-columns`: style.css=`minmax(0, 1fr) minmax(0, 1fr)` vs pixel.css=`minmax(0, 1fr)`
- **Apenas no style.css** (7): display, gap, margin-bottom, margin-inline, max-width, padding, width

### `decoder-content` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (3): animation, border-color, box-shadow

### `decoder-feedback` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `animation`: style.css=`decoderFeedbackIn 0.3s ease-out` vs pixel.css=`none`
- **Apenas no style.css** (9): background, border, border-radius, color, font-size, font-weight, padding, text-align, width

### `decoder-hint` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(253, 224, 71, 0.08)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(253, 224, 71, 0.3)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `decoder-hint-label` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `decoder-hint-value` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--hint-yellow)` vs pixel.css=`var(--text-main)`

### `decoder-input` [NAO-NOVO-DESIGN]
- style.css: 13 props | pixel.css: 11 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`rgba(255, 255, 255, 0.05)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): border-color, opacity

### `decoder-input-row` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `decoder-stat` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`
  - `font-weight`: style.css=`800` vs pixel.css=`600`

### `decoder-stats` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.03)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `decoder-timer-bar` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`linear-gradient(90deg, var(--error-red), var(--warning-orange))` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`5px` vs pixel.css=`0`
- **Apenas no style.css** (1): animation

### `decoder-timer-container` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.08)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`5px` vs pixel.css=`0`

### `decoder-timer-text` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`#fff` vs pixel.css=`var(--text-main)`

### `decoder-txid` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 12 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`rgba(247, 147, 26, 0.08)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--btc-orange)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `energy-bar-container` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `energy-bar-fill` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`linear-gradient(90deg, var(--error-red), var(--warning-orange))` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`
  - `box-shadow`: style.css=`0 0 8px rgba(239, 68, 68, 0.3)` vs pixel.css=`0 0 8px rgba(250, 204, 21, 0.3)`
- **Apenas no style.css** (1): animation

### `energy-bar-track` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.06)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `energy-count` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`

### `energy-item` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(250, 204, 21, 0.06)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): color

### `energy-label` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`

### `energy-timer` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `found` [NOVO-DESIGN]
- style.css: 5 props | pixel.css: 6 props | novo design: 6 props
- pixel.css alinhamento: 100% novo-design / 17% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`rgba(34, 197, 94, 0.12)` vs pixel.css=`rgba(0, 255, 136, 0.12)`
  - `border-color`: style.css=`rgba(34, 197, 94, 0.45)` vs pixel.css=`rgba(0, 255, 136, 0.4)`
  - `color`: style.css=`var(--text-main)` vs pixel.css=`var(--neon-green)`
  - `opacity`: style.css=`0.38` vs pixel.css=`0.25`
- **Apenas no pixel.css** (1): border-left-color

### `friends-add-form` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (2): display, gap
- **Apenas no pixel.css** (1): flex-direction

### `friends-add-input` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `friends-add-section` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `friends-coop-bonus` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`rgba(34, 197, 94, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(34, 197, 94, 0.3)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `friends-list` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `friends-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `game-area` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `gap`: style.css=`12px` vs pixel.css=`24px`
  - `grid-template-columns`: style.css=`minmax(0, 1fr)` vs pixel.css=`minmax(190px, 240px) minmax(0, 1fr)`
  - `order`: style.css=`1` vs pixel.css=`initial`
- **Apenas no style.css** (3): display, min-width, scroll-margin-top
- **Apenas no pixel.css** (1): grid-column

### `game-instructions` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): font-size, line-height, text-align
- **Apenas no pixel.css** (2): background, border

### `game-status` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (5): color, font-size, line-height, min-height, text-align
- **Apenas no pixel.css** (1): grid-column

### `glass-panel` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`12px` vs pixel.css=`0`

### `global-event-banner` [NAO-NOVO-DESIGN]
- style.css: 14 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (7): background, border-bottom-color, border-color, color, opacity, pointer-events, transform

### `global-event-banner-inner` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `gap`: style.css=`12px` vs pixel.css=`8px`
  - `padding`: style.css=`12px 20px` vs pixel.css=`8px 12px`
- **Apenas no style.css** (5): align-items, backdrop-filter, background, border-bottom, display

### `global-event-countdown` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `font-size`: style.css=`20px` vs pixel.css=`16px`
  - `padding`: style.css=`4px 12px` vs pixel.css=`2px 8px`
- **Apenas no style.css** (7): background, border, border-color, border-radius, color, font-family, font-weight

### `global-event-description` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`12px` vs pixel.css=`11px`
- **Apenas no style.css** (2): color, margin-top

### `global-event-dismiss` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `global-event-icon` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`32px` vs pixel.css=`24px`
- **Apenas no style.css** (2): animation, flex-shrink

### `global-event-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `global-event-label` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`16px` vs pixel.css=`13px`
- **Apenas no style.css** (4): color, font-weight, letter-spacing, text-transform

### `global-event-timer` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `grid-overlay` [NOVO-DESIGN]
- style.css: 12 props | pixel.css: 9 props | novo design: 9 props
- pixel.css alinhamento: 100% novo-design / 78% style.css
- **Propriedades CONFLITANTES** (1):
  - `background`: style.css=`rgba(5, 5, 5, 0.84)` vs pixel.css=`rgba(14, 17, 23, 0.94)`
- **Apenas no style.css** (4): backdrop-filter, border-radius, padding, text-align
- **Apenas no pixel.css** (1): gap

### `grid-wrapper` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `min-height`: style.css=`min(480px, 80vh)` vs pixel.css=`470px`
  - `padding`: style.css=`10px` vs pixel.css=`18px`
- **Apenas no style.css** (8): align-items, contain, display, justify-content, min-width, overflow, position, width

### `halving` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--high-fee)` vs pixel.css=`var(--text-main)`

### `halving-flash` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `hidden` [MIXTO]
- style.css: 4 props | pixel.css: 1 props | novo design: 1 props
- pixel.css alinhamento: 100% novo-design / 100% style.css
- **Apenas no style.css** (3): opacity, pointer-events, transform

### `hint-glow` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `border-color`: style.css=`var(--hint-yellow)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--hint-yellow)` vs pixel.css=`var(--text-main)`

### `leaderboard-list` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (3): display, gap, grid-template-columns
- **Apenas no pixel.css** (3): background, border, color

### `level-bar-container` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `level-bar-fill` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`linear-gradient(90deg, var(--btc-orange), #f59e0b)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`12px` vs pixel.css=`0`

### `level-bar-text` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`#fff` vs pixel.css=`var(--text-main)`

### `level-bar-track` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`12px` vs pixel.css=`0`

### `level-icon` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `level-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (4): align-items, display, gap, margin-bottom
- **Apenas no pixel.css** (1): flex-wrap

### `level-name` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`14px` vs pixel.css=`12px`
- **Apenas no style.css** (3): color, flex, font-weight

### `level-value` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `font-size`: style.css=`14px` vs pixel.css=`12px`
- **Apenas no style.css** (3): animation, color, font-weight

### `leveled-up` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `lightning-item` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(14, 165, 233, 0.06)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): color

### `lightning-theme` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (4): background, border-color, box-shadow, color

### `loader-spinner` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `border`: style.css=`3px solid rgba(247, 147, 26, 0.2)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`50%` vs pixel.css=`0`
  - `border-top-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `loader-text` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): max-width

### `loading-state` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `low` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): animation, background, box-shadow

### `main-layout` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `gap`: style.css=`14px` vs pixel.css=`24px`
  - `grid-template-columns`: style.css=`minmax(0, 1fr)` vs pixel.css=`260px minmax(0, 1fr) 260px`
- **Apenas no style.css** (5): display, margin-inline, max-width, padding-bottom, width
- **Apenas no pixel.css** (1): min-height

### `market-filters` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `market-inventory` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `market-listings` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `market-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `market-sales-history` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `market-section` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (1): display

### `market-sell-form` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `market-sell-input` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `market-sell-select` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `market-tab-btn` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--btc-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): border-color

### `market-tabs` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `miner-input` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
- **Apenas no style.css** (6): border-color, margin-bottom, min-height, outline, text-align, width

### `miner-name` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `mining-stats` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `grid-column`: style.css=`1 / -1` vs pixel.css=`1`
- **Apenas no style.css** (4): display, gap, grid-template-columns, text-align

### `missions-list` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `missions-panel` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (2): display, flex-direction
- **Apenas no pixel.css** (2): max-height, overflow-y

### `mobile-nav` [NAO-NOVO-DESIGN]
- style.css: 16 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `display`: style.css=`flex` vs pixel.css=`none`
- **Apenas no style.css** (15): align-items, border-radius, bottom, color, font-size, font-weight, grid-template-columns, justify-content, left, min-height...

### `mobile-nav-btn` [NAO-NOVO-DESIGN]
- style.css: 12 props | pixel.css: 12 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`transparent` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`none` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `modal-content` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `padding`: style.css=`26px 18px` vs pixel.css=`36px`
- **Apenas no style.css** (7): border-radius, max-height, overflow-y, text-align, transform, transition, width

### `modal-overlay` [NAO-NOVO-DESIGN]
- style.css: 15 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (14): align-items, backdrop-filter, background, display, inset, justify-content, opacity, overflow-y, padding, pointer-events...

### `modal-text` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `modal-title` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): font-size, font-weight, margin-bottom

### `mt-auto` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `network-badge` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `network-label` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (5): display, letter-spacing, margin-bottom, text-align, text-transform

### `network-select` [NAO-NOVO-DESIGN]
- style.css: 14 props | pixel.css: 11 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--bg-dark)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
- **Apenas no style.css** (3): border-color, cursor, opacity

### `network-status` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `node-status` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `offline` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `border-color`: style.css=`rgba(239, 68, 68, 0.5)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`#fecaca` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): background

### `panel-header` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pool-tag-input` [NAO-NOVO-DESIGN]
- style.css: 14 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (10): background, border, border-radius, color, margin-bottom, min-height, outline, padding, text-align, width

### `pool-tag-label` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `powerups-active` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `powerups-bar-container` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`

### `powerups-header` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `powerups-label` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-actions` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-challenge-form` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (6): background, border, border-radius, color, font-size, padding

### `pvp-challenged-card` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`

### `pvp-challenger-card` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `pvp-countdown-content` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-countdown-number` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `pvp-countdown-words` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-match-info` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-player-card` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`

### `pvp-player-found` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-player-label` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-player-name` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-player-score` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--golden-hash)` vs pixel.css=`var(--text-main)`

### `pvp-progress-bar-container` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `pvp-progress-container` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-progress-fill` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-progress-fill-challenged` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `background`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--hull-surface)`

### `pvp-progress-fill-challenger` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `background`: style.css=`var(--btc-orange)` vs pixel.css=`var(--hull-surface)`

### `pvp-progress-label` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-result-content` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`

### `pvp-result-icon` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-result-scores` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--golden-hash)` vs pixel.css=`var(--text-main)`

### `pvp-result-text` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-result-title` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-status` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `pvp-status-text` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-timer-bar` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`linear-gradient(90deg, var(--btc-orange), var(--warning-orange))` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`3px` vs pixel.css=`0`

### `pvp-timer-bar-container` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`3px` vs pixel.css=`0`

### `pvp-timer-text` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `pvp-vs-badge` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`

### `race-bar-network` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `background`: style.css=`var(--error-red)` vs pixel.css=`var(--hull-surface)`

### `race-track` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`rgba(255, 255, 255, 0.06)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`3px` vs pixel.css=`0`
- **Apenas no style.css** (3): margin-inline, max-width, width

### `revealed` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `reward` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `animation`: style.css=`decoderReward 0.6s ease-out` vs pixel.css=`none`
- **Apenas no style.css** (2): border-color, box-shadow

### `season-content` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-header` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-label` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `season-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `season-progress` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-progress-bar` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`var(--glass-bg)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `season-progress-fill` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (2):
  - `background`: style.css=`linear-gradient(90deg, var(--btc-orange), #ffd700)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`4px` vs pixel.css=`0`

### `season-progress-text` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `season-rewards-list` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-tab` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--btc-orange)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`#000` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): border-color, font-weight

### `season-tabs` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `season-timer` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `season-value` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `selected` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(14, 165, 233, 0.22)` vs pixel.css=`var(--hull-surface)`
  - `border-color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`
  - `color`: style.css=`var(--lightning-blue)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): contain, transform, z-index

### `session-submit` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `side-panel` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (3): min-width, padding, width
- **Apenas no pixel.css** (3): background, border, color

### `skills-branches` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `skills-content` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `skills-header` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `skills-level-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `skills-level-label` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `skills-level-value` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `skills-panel` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (2): display, flex-direction
- **Apenas no pixel.css** (2): max-height, overflow-y

### `skills-points-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (4): align-items, display, font-size, gap
- **Apenas no pixel.css** (3): background, border, color

### `skills-points-label` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`
- **Apenas no pixel.css** (2): background, border

### `skills-points-value` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `skip-link` [NAO-NOVO-DESIGN]
- style.css: 10 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (4):
  - `background`: style.css=`var(--text-main)` vs pixel.css=`var(--hull-surface)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
  - `color`: style.css=`var(--bg-dark)` vs pixel.css=`var(--text-main)`
  - `transform`: style.css=`translateY(0)` vs pixel.css=`translateY(-180%)`

### `slashing-flash` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `sprint-leaderboard-list` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (1): padding

### `sprint-panel` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `padding`: style.css=`16px` vs pixel.css=`12px`
- **Apenas no pixel.css** (2): max-height, overflow-y

### `sprint-timer` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): animation, text-shadow

### `sprint-timer-container` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (6): left, pointer-events, position, top, transform, z-index

### `staking-active` [NAO-NOVO-DESIGN]
- style.css: 7 props | pixel.css: 7 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(247, 147, 26, 0.06)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--btc-orange)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`

### `staking-amount-input` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-bonus` [NAO-NOVO-DESIGN]
- style.css: 1 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green) !important` vs pixel.css=`var(--text-main)`

### `staking-countdown` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(247, 147, 26, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(247, 147, 26, 0.2)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`

### `staking-countdown-label` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-countdown-value` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (4): color, font-size, font-variant-numeric, font-weight
- **Apenas no pixel.css** (1): animation

### `staking-desc` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-duration-bonus` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`

### `staking-duration-btn` [NAO-NOVO-DESIGN]
- style.css: 14 props | pixel.css: 13 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(247, 147, 26, 0.1)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
- **Apenas no style.css** (1): border-color

### `staking-duration-value` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-durations` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-form` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-history` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-history-list` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-history-title` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-info-label` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-info-row` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-info-value` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-input` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 10 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.05)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`6px` vs pixel.css=`0`
- **Apenas no style.css** (1): border-color

### `staking-label` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-panel` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-status-bar` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `staking-status-label` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `staking-status-value` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `staking-warning` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--warning-orange)` vs pixel.css=`var(--text-main)`

### `stat-box` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `stat-val` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 4 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--high-fee)` vs pixel.css=`var(--text-main)`

### `store-desc` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `store-info` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `store-item` [NAO-NOVO-DESIGN]
- style.css: 8 props | pixel.css: 8 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(255, 255, 255, 0.03)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid var(--glass-border)` vs pixel.css=`1px solid var(--border-hi)`
  - `border-radius`: style.css=`8px` vs pixel.css=`0`

### `store-panel` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `store-title` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--energy-yellow)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (2): font-size, font-weight

### `svg-lines` [NAO-NOVO-DESIGN]
- style.css: 6 props | pixel.css: 6 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `unlocked` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border-color`: style.css=`var(--success-green)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (3): background, box-shadow, color

### `update-actions` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `update-banner` [NAO-NOVO-DESIGN]
- style.css: 11 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `bottom`: style.css=`calc(74px + max(12px, env(safe-area-inset-bottom)))` vs pixel.css=`max(18px, env(safe-area-inset-bottom))`
- **Apenas no style.css** (10): color, display, flex-direction, gap, left, max-width, padding, position, right, z-index

### `urgent` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `animation`: style.css=`decoderTimerPulse 0.5s ease-in-out infinite` vs pixel.css=`none`
- **Apenas no style.css** (1): background

### `visible` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css

### `visually-hidden` [NAO-NOVO-DESIGN]
- style.css: 9 props | pixel.css: 9 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `border`: style.css=`0` vs pixel.css=`1px solid var(--border-hi)`

### `wallet-balance` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--btc-orange)` vs pixel.css=`var(--text-main)`

### `wallet-info` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Apenas no style.css** (4): display, flex-direction, gap, min-width
- **Apenas no pixel.css** (3): background, border, color

### `wallet-label` [NAO-NOVO-DESIGN]
- style.css: 5 props | pixel.css: 5 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--text-muted)` vs pixel.css=`var(--text-main)`

### `warning` [NAO-NOVO-DESIGN]
- style.css: 2 props | pixel.css: 2 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `color`: style.css=`var(--error-red)` vs pixel.css=`var(--text-main)`

### `weekly` [NAO-NOVO-DESIGN]
- style.css: 4 props | pixel.css: 3 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (3):
  - `background`: style.css=`rgba(234, 179, 8, 0.15)` vs pixel.css=`var(--hull-surface)`
  - `border`: style.css=`1px solid rgba(234, 179, 8, 0.3)` vs pixel.css=`1px solid var(--border-hi)`
  - `color`: style.css=`var(--golden-hash)` vs pixel.css=`var(--text-main)`
- **Apenas no style.css** (1): border-color

### `word-bank` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `padding`: style.css=`16px` vs pixel.css=`20px`
- **Apenas no style.css** (2): min-width, width

### `word-bank-list` [NAO-NOVO-DESIGN]
- style.css: 3 props | pixel.css: 1 props | novo design: 0 props
- pixel.css alinhamento: -% novo-design / -% style.css
- **Propriedades CONFLITANTES** (1):
  - `grid-template-columns`: style.css=`repeat(2, minmax(0, 1fr))` vs pixel.css=`minmax(0, 1fr)`
- **Apenas no style.css** (2): display, gap

### `word-grid` [NOVO-DESIGN]
- style.css: 10 props | pixel.css: 5 props | novo design: 5 props
- pixel.css alinhamento: 100% novo-design / 40% style.css
- **Propriedades CONFLITANTES** (1):
  - `gap`: style.css=`var(--grid-gap)` vs pixel.css=`3px`
- **Apenas no style.css** (7): --cell-size, --grid-gap, -webkit-user-select, animation, box-shadow, justify-content, user-select
- **Apenas no pixel.css** (2): height, width
