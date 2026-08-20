# PLANO DE AÇÃO — Aplicar Novo Design Mecha Sci-Fi Industrial

**Data:** 19 de agosto de 2026  
**Design Fonte:** `new-design.html` (1306 linhas, tema Mecha Sci-Fi Industrial escuro)  
**Código Atual:** `frontend/index.html` (800 linhas), `frontend/game.js` (6170 linhas), `frontend/style.css` (4000+ linhas)

---

## Diagnóstico

| Métrica | Atual | Novo Design | Gap |
|---------|-------|-------------|-----|
| IDs no HTML | 254 | 31 | -223 IDs |
| IDs no game.js | 165 | 31 | -134 IDs |
| Classes CSS | 286 | 45 | -241 classes |
| Tema | Pixel Art claro/bege | Mecha Sci-Fi escuro | 100% diferente |
| Layout | 5 tabs (JOGO, UPGRADES, COMPETIR, PERFIL, SOCIAL) | 4 abas (TX, SHOP, RANK, INFO) | Estrutura diferente |
| Fontes | Press Start 2P, VT323, Pixelify Sans | JetBrains Mono, Press Start 2P, VT323 | 1 fonte nova |

### Classes Compartilhadas (4)
- `active`, `hidden`, `cell`, `found`

### Classes Mapeadas (33)
- Classes do novo design que substituem classes atuais

### Classes Novas (15)
- Classes do novo design que precisam ser criadas

### Classes Removíveis (75)
- Classes atuais que não existem no novo design

---

## Estratégia de Aplicação

### Princípios
1. **Seguir 100% o design** — sem alterar, ajustar ou remover elementos visuais do novo design
2. **Respeitar a lógica ativa** — manter todas as mecânicas funcionais do game.js
3. **Adicionar mecânicas ao design** — incluir IDs faltantes no HTML do novo design
4. **Não quebrar o sistema** — aplicar em fases com health check entre cada uma

### Abordagem
- **Fase 1:** CSS — Reescrever pixel.css com tema Mecha Sci-Fi Industrial
- **Fase 2:** HTML — Reescrever index.html baseado no novo design + IDs faltantes
- **Fase 3:** JS — Adaptar game.js para novos IDs
- **Fase 4:** Integração — Rebuild e testes

---

## Fase 1: CSS — Tema Mecha Sci-Fi Industrial

### Objetivo
Reescrever `pixel.css` com o CSS completo do novo design + aliases para classes do game.js.

### Ações
1. Extrair CSS completo do `new-design.html` (~20KB)
2. Adicionar `@import` para JetBrains Mono
3. Criar aliases para 286 classes atuais → classes do novo design
4. Manter classes de mecânicas avançadas (achievements, boss, decoder, etc.)

### Mapeamento de Cores
| Variável Atual | Nova Variável | Cor |
|----------------|---------------|-----|
| `--bg-canvas: #f0deaf` | `--bg-void: #0e1117` | Fundo escuro |
| `--bg-panel: #e2c992` | `--hull-dark: #161b22` | Painéis |
| `--bg-card: #faedd0` | `--hull-surface: #272d38` | Cards |
| `--ink: #26163b` | `--text-main: #f0f6fc` | Texto |
| `--btc-gold: #c87600` | `--neon-amber: #f7931a` | Bitcoin |
| `--neon-green: #1b8a3e` | `--neon-green: #00ff88` | Sucesso |
| `--neon-red: #ba1c2c` | `--neon-red: #ff3355` | Erro |
| `--neon-cyan: #097b9c` | `--neon-cyan: #00f0ff` | Destaque |

### Mapeamento de Classes Principais
| Classe Atual | Classe Novo Design | Ação |
|--------------|-------------------|------|
| `.dashboard` | `.hud-header` | Renomear |
| `.game-area` | `.stage-center` | Renomear |
| `.grid-wrapper` | `.grid-hull` | Renomear |
| `.word-grid` | `.word-grid` | Manter |
| `.cell` | `.cell` | Manter (restyle) |
| `.word-bank-list` | `.tx-list-container` | Renomear |
| `.race-track` | `.race-box` | Renomear |
| `.race-fill` | `.race-bar` | Renomear |
| `.modal-overlay` | `.modal-wrap` | Renomear |
| `.modal-content` | `.modal-mecha-box` | Renomear |
| `.btn` | `.mecha-btn` | Renomear |
| `.store-item` | `.shop-card-mecha` | Renomear |
| `.panel-scroll` | `.tab-pane` | Renomear |
| `.sidebar-nav` | `.mecha-nav-group` | Renomear |
| `.nav-btn` | `.mecha-btn` | Renomear |
| `.mobile-nav` | (remover) | Novo design não tem mobile nav separado |
| `.tab-content` | `.tab-pane` | Renomear |
| `.content-area` | `.hud-body` | Renomear |
| `.content-body` | `.sidebar-right` | Renomear |
| `.content-header` | `.panel-code-tag` | Renomear |
| `.main-layout` | `.mecha-frame` | Renomear |

### Estimativa
- **Esforço:** 1 hora
- **Risco:** Baixo (CSS não quebra lógica)

---

## Fase 2: HTML — Estrutura Mecha Frame

### Objetivo
Reescrever `index.html` baseado no novo design + adicionar IDs faltantes para mecânicas ativas.

### Estrutura do Novo HTML
```
.mecha-frame
├── .side-rail (left/right) — Decorativo
├── .hud-header
│   ├── .hud-title-zone (SYS tag + operator)
│   └── .hud-metrics (balance, block, combo, hw)
├── .hud-body
│   ├── .stage-center
│   │   ├── .race-box (corrida contra rede)
│   │   └── .grid-hull (grid + overlay + SVG)
│   └── .sidebar-right
│       ├── .panel-code-tag
│       ├── .mecha-nav-group (4 botões de aba)
│       ├── #tab-tx (lista de TXs)
│       ├── #tab-shop (loja de upgrades)
│       ├── #tab-rank (leaderboard + pools)
│       └── #tab-info (protocol info)
├── .hud-footer (status)
├── #auth-modal (login)
└── #result-modal (resultado)
```

### IDs a Adicionar (149 faltantes)

#### Prioridade 1 — Core (sem estes o jogo não funciona)
- `tx-list-container` → word bank (já existe no novo design)
- `race-fill` → race bar (já existe)
- `ui-operator-tag` → nome do minerador (já existe)
- `ui-hw` → hardware (já existe)
- `btn-buy-ln` → lightning (já existe)
- `auth-modal` → login (já existe)
- `result-modal` → resultado (já existe)
- `result-title`, `result-text` → modal resultado (já existem)
- `pool-list` → pools (já existe)
- `leaderboard-list` → leaderboard (já existe)

#### Prioridade 2 — Mecânicas Ativas (adicionar ao HTML)
- **Achievements:** `achievement-toast`, `achievements-modal`, `achievements-grid`, `achievements-filters`, `achievements-summary`
- **Boss Battles:** `boss-hud`, `boss-hp-bar`, `boss-hp-text`, `boss-defeat-modal`
- **Decoder:** `decoder-modal`, `decoder-input`, `decoder-feedback`, `decoder-timer-bar`, `decoder-timer-text`, `decoder-streak`, `decoder-wins`, `decoder-txid`, `decoder-hint-letter`
- **Skills Tree:** `skills-panel`, `skills-content`, `skills-header`, `skills-loading`, `skills-level-value`, `skills-points-value`
- **Level System:** `level-bar-container`, `level-bar-fill`, `level-bar-text`, `level-icon`, `level-name`, `level-value`
- **Chat:** `chat-panel`, `chat-messages`, `chat-input`, `chat-send-btn`, `chat-emoji-bar`, `chat-rate-info`
- **Staking:** `staking-panel`, `staking-form`, `staking-amount-input`, `staking-duration`, `staking-bonus`, `staking-timer`, `staking-active`, `staking-history-list`
- **Friends:** `friends-panel`, `friends-list`, `friends-add-input`, `friends-loading`, `friends-coop-bonus`
- **Market:** `market-panel`, `market-browse`, `market-sell`, `market-filter-powerup`, `market-history`, `market-sell-select`, `market-sell-price`
- **Season Pass:** `season-panel`, `season-content`, `season-loading`, `season-progress-bar`, `season-progress-fill`, `season-progress-text`, `season-rewards-free`, `season-rewards-premium`, `season-timer`, `season-id-value`, `season-level-value`, `season-xp-value`
- **Cards:** `cards-panel`, `cards-grid`, `cards-loading`, `cards-total`, `cards-common`, `cards-rare`, `cards-epic`, `cards-legendary`, `cards-bonus`
- **Global Events:** `global-event-banner`, `global-event-icon`, `global-event-label`, `global-event-description`, `global-event-countdown`
- **Sprint Mode:** `sprint-timer-display`, `sprint-timer-value`, `sprint-leaderboard-list`
- **Crates:** `crate-icon`, `crate-free-count`
- **Powerups:** `powerups-bar-container`
- **Energy:** `ui-energy-bar`, `ui-energy-count`, `ui-energy-timer`
- **PWA:** `btn-install-app`, `pwa-update-banner`, `btn-update-app`, `btn-dismiss-update`
- **Network:** `connectivity-status`, `game-status`

#### IDs a Remover (10)
- `network-select`, `network-status`, `btn-start-session`, `ui-active-network`, `btn-change-network` — Nova design não tem seleção de rede
- `lightning-modal`, `lightning-text` — Nova design ativa Lightning inline
- `pool-tag-input` — Nova design usa `[TAG] NOME` no input único
- `next-btn` — Nova design usa botão inline no `result-box`
- `tutorial-modal`, `tutorial-form` — Substituídos por `auth-modal`

### Estimativa
- **Esforço:** 2 horas
- **Risco:** Médio (mudança de estrutura HTML)

---

## Fase 3: JS — Adaptar game.js

### Objetivo
Adaptar `game.js` para usar novos IDs e classes do design Mecha.

### Mapeamento de IDs no game.js
```javascript
// Substituir no game.js:
'word-bank-list' → 'tx-list-container'
'ui-network-progress' → 'race-fill'
'ui-miner-name' → 'ui-operator-tag'
'ui-hardware' → 'ui-hw'
'btn-buy-lightning' → 'btn-buy-ln'
'tutorial-modal' → 'auth-modal'
'pools-list' → 'pool-list'
'btn-buy-hint' → 'btn-buy-hint' (já existe)
'btn-buy-hw' → 'btn-buy-hw' (já existe)
'hw-title' → 'hw-title' (já existe)
'result-modal' → 'result-modal' (já existe)
'result-title' → 'result-title' (já existe)
'result-text' → 'result-text' (já existe)
'miner-input' → 'miner-input' (já existe)
'leaderboard-list' → 'leaderboard-list' (já existe)
'ui-balance' → 'ui-balance' (já existe)
'ui-block' → 'ui-block' (já existe)
'ui-combo' → 'ui-combo' (já existe)
'word-grid' → 'word-grid' (já existe)
'lines-svg' → 'lines-svg' (já existe)
'grid-wrapper' → 'grid-hull'
'grid-overlay' → 'grid-overlay' (já existe)
'tx-loading' → 'tx-loading' (já existe)
'auth-modal' → 'auth-modal' (já existe)
'ui-operator-tag' → 'ui-operator-tag' (já existe)
```

### Funções a Modificar
1. `showTab()` → `switchTab()` (nova função do design)
2. `startSession()` → Manter (já existe no novo design)
3. `prepareNextBlock()` → Manter
4. `buildBlock()` → Manter
5. `endSelection()` → Manter
6. `showResult()` → Adaptar para novo modal
7. `updateLeaderboard()` → Adaptar para novo layout
8. `updateStore()` → Adaptar para nova loja

### Classes a Substituir no game.js
```javascript
// Substituir classList:
'active' → 'active' (manter)
'hidden' → 'hidden' (manter)
'found' → 'found' (manter)
'sel' → 'sel' (manter)
'mev-found' → 'mev-found' (manter)
'hint' → 'hint' (manter)
'blink' → 'blink' (remover, novo design não usa)
'float-pts' → 'float-pts' (manter)
```

### Estimativa
- **Esforço:** 3 horas
- **Risco:** Alto (mudança de lógica JS)

---

## Fase 4: Integração — Rebuild e Testes

### Objetivo
Rebuildar containers e verificar funcionalidade.

### Ações
1. Atualizar `Dockerfile` para incluir novas fontes
2. Atualizar `.dockerignore`
3. Rebuildar container do frontend
4. Health check completo (16 testes)
5. Testar todas as mecânicas ativas

### Estimativa
- **Esforço:** 30 minutos
- **Risco:** Baixo

---

## Ordem de Execução

1. **Fase 1:** CSS (pixel.css) — 1 hora
2. **Fase 2:** HTML (index.html) — 2 horas
3. **Fase 3:** JS (game.js) — 3 horas
4. **Fase 4:** Integração — 30 minutos

**Total estimado:** 6 horas e 30 minutos

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| IDs faltantes quebram game.js | Alto | Mapear todos os 149 IDs antes de aplicar |
| Classes CSS conflitantes | Médio | Usar !important apenas quando necessário |
| Layout responsivo quebrado | Médio | Testar em todos os breakpoints |
| Mecânicas avançadas sem UI | Baixo | Adicionar IDs faltantes ao HTML |
| Backend incompatível | Baixo | Backend não precisa de mudanças |

---

## Próximos Passos

1. **Aprovar plano** — Usuário aprova o plano de ação
2. **Aplicar Fase 1** — Reescrever pixel.css
3. **Health check** — Verificar CSS
4. **Aplicar Fase 2** — Reescrever index.html
5. **Health check** — Verificar HTML
6. **Aplicar Fase 3** — Adaptar game.js
7. **Health check** — Verificar JS
8. **Aplicar Fase 4** — Rebuild e testes
9. **Auditoria final** — Delegar agent de auditoria
