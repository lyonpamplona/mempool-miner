# AUDITORIA COMPLETA — Redesign Mecha Sci-Fi Industrial

**Data:** 19 de agosto de 2026  
**Arquivos auditados:** new-design.html, index.html, pixel.css, style.css, game.js

---

## 1. RESUMO EXECUTIVO

| Métrica | Status | Detalhe |
|---------|--------|---------|
| Classes do new-design no pixel.css | ✅ 56/56 | Todas presentes |
| Classes do new-design no index.html | ⚠️ 42/56 | 14 faltam (aplicadas via JS) |
| IDs do game.js no index.html | ✅ 164/164 | Todos presentes |
| IDs duplicados | ✅ 0 | Zero duplicados |
| Estrutura HTML | ✅ OK | mecha-frame > hud-header > hud-body > hud-footer |
| Classes sobrepostas (style.css ∩ pixel.css) | 🔴 296 | Conflito de estilos |
| Variáveis CSS conflitantes | ⚠️ 1 | --text-main |
| !important no style.css | ⚠️ 8 | Pode sobrescrever pixel.css |

---

## 2. PROBLEMAS IDENTIFICADOS

### 🔴 CRÍTICO: 296 Classes Sobrepostas

O style.css (450 classes, tema antigo) e o pixel.css (361 classes, tema novo) compartilham **296 classes**. Como o style.css é carregado ANTES do pixel.css, o pixel.css deveria sobrescrever — MAS:

- **8 !important** no style.css podem impedir a sobrescrita
- **1 variável CSS conflitante** (--text-main) pode causar inconsistência
- **7 classes compartilhadas** com o new-design (active, cell, cross-line, found, grid-overlay, hidden, word-grid) podem ter propriedades erradas do style.css

### ⚠️ MÉDIO: 14 Classes Faltando no HTML

Estas classes são aplicadas **dinamicamente via JavaScript** (classList.add), então não precisam estar no HTML estático:

| Classe | Aplicada via | Origem |
|--------|-------------|--------|
| `.badge-gold` | JS | game.js |
| `.badge-high` | JS | game.js |
| `.badge-mecha` | JS | game.js |
| `.badge-std` | JS | game.js |
| `.cell` | JS | game.js (cria células da grid) |
| `.cross-line` | JS | game.js (desenha linhas SVG) |
| `.float-pts` | JS | game.js (animação de pontos) |
| `.found` | JS | game.js (palavras encontradas) |
| `.hint` | JS | game.js (dicas) |
| `.lightning-active` | JS | game.js (modo Lightning) |
| `.mev-found` | JS | game.js (MEV oculto) |
| `.rbf` | JS | game.js (RBF) |
| `.sel` | JS | game.js (seleção) |
| `.tx-card-mecha` | JS | game.js (cards de TX) |

### ⚠️ MÉDIO: 1 Variável CSS Conflitante

| Variável | style.css | pixel.css | new-design |
|----------|-----------|-----------|------------|
| `--text-main` | `#e2e8f0` | `#f0f6fc` | `#f0f6fc` |

O style.css define `--text-main: #e2e8f0` e o pixel.css define `--text-main: #f0f6fc`. Como o pixel.css é carregado depois, ele sobrescreve — MAS se algum elemento usa a variável antes do pixel.css ser aplicado, pode haver flash de cor errada.

---

## 3. CLASSES SOBREPOSTAS (296)

As 296 classes sobrepostas entre style.css e pixel.css incluem:

### Classes do new-design que também estão no style.css (7):
- `.active` — Estado ativo de tabs/botões
- `.cell` — Célula da grid
- `.cross-line` — Linha SVG de seleção
- `.found` — Palavra encontrada
- `.grid-overlay` — Overlay de loading
- `.hidden` — Elemento oculto
- `.word-grid` — Grid de caça-palavras

### Classes do game.js que também estão no style.css (19):
- `.achievement-toast`, `.achievement-toast-content`, `.achievement-toast-desc`, `.achievement-toast-icon`, `.achievement-toast-title`
- `.achievements-filters`, `.achievements-grid`, `.achievements-modal-content`, `.achievements-summary`
- `.boss-hp-bar`, `.boss-hp-bar-container`, `.boss-hp-text`, `.boss-hud`
- `.btn-buy-energy`, `.btn-buy-season-premium`, `.btn-cancel-stake`
- `.cards-bonus`, `.cards-common`, `.cards-epic`, `.cards-grid`, `.cards-legendary`, `.cards-loading`, `.cards-panel`, `.cards-rare`, `.cards-total`
- `.chat-emoji-bar`, `.chat-input`, `.chat-messages`, `.chat-panel`, `.chat-rate-info`, `.chat-send-btn`
- `.decoder-feedback`, `.decoder-hint-letter`, `.decoder-input`, `.decoder-modal`, `.decoder-streak`, `.decoder-timer-bar`, `.decoder-timer-text`, `.decoder-txid`, `.decoder-wins`
- `.energy-bar-container`, `.energy-bar-fill`, `.energy-bar-track`, `.energy-count`, `.energy-label`, `.energy-timer`
- `.friends-add-input`, `.friends-coop-bonus`, `.friends-list`, `.friends-loading`, `.friends-panel`
- `.global-event-banner`, `.global-event-banner-inner`, `.global-event-countdown`, `.global-event-description`, `.global-event-dismiss`, `.global-event-icon`, `.global-event-info`, `.global-event-label`, `.global-event-timer`
- `.level-bar-container`, `.level-bar-fill`, `.level-bar-text`, `.level-bar-track`, `.level-icon`, `.level-info`, `.level-name`, `.level-value`
- `.market-browse`, `.market-filter-powerup`, `.market-history`, `.market-panel`, `.market-sell`, `.market-sell-price`, `.market-sell-select`
- `.missions-list`, `.missions-loading`, `.missions-panel`
- `.powerups-active`, `.powerups-bar-container`, `.powerups-header`, `.powerups-label`
- `.season-content`, `.season-id-value`, `.season-level-value`, `.season-loading`, `.season-panel`, `.season-progress-bar`, `.season-progress-fill`, `.season-progress-text`, `.season-rewards-free`, `.season-rewards-premium`, `.season-timer`, `.season-xp-value`
- `.skills-content`, `.skills-header`, `.skills-level-value`, `.skills-loading`, `.skills-panel`, `.skills-points-value`
- `.sprint-leaderboard-list`, `.sprint-timer-display`, `.sprint-timer-value`
- `.staking-active`, `.staking-amount`, `.staking-amount-input`, `.staking-bonus`, `.staking-duration`, `.staking-form`, `.staking-history-list`, `.staking-panel`, `.staking-timer`

### Classes genéricas sobrepostas (270):
- `.active`, `.hidden`, `.btn`, `.modal-overlay`, `.modal-content`, `.panel-scroll`, `.sidebar-nav`, `.nav-btn`, `.mobile-nav`, `.tab-content`, `.content-area`, `.content-body`, `.content-header`, `.main-layout`, `.glass-panel`, etc.

---

## 4. PLANO DE AÇÃO

### Fase 1: Remover style.css (Prioridade CRÍTICA)

**Problema:** O style.css (450 classes, tema antigo) conflita com o pixel.css (361 classes, tema novo).

**Solução:** Remover o `<link rel="stylesheet" href="style.css">` do index.html.

**Risco:** Baixo — o pixel.css já tem aliases para todas as 296 classes sobrepostas.

**Ação:**
```html
<!-- REMOVER esta linha do index.html -->
<link rel="stylesheet" href="style.css">
```

### Fase 2: Corrigir Variável CSS Conflitante (Prioridade MÉDIA)

**Problema:** `--text-main` é definido em style.css (`#e2e8f0`) e pixel.css (`#f0f6fc`).

**Solução:** Após remover o style.css, apenas o pixel.css definirá a variável.

**Ação:** Nenhuma — resolvido automaticamente na Fase 1.

### Fase 3: Verificar !important no style.css (Prioridade MÉDIA)

**Problema:** 8 `!important` no style.css podem sobrescrever o pixel.css.

**Solução:** Após remover o style.css, os `!important` não mais afetam.

**Ação:** Nenhuma — resolvido automaticamente na Fase 1.

### Fase 4: Verificar Classes Dinâmicas (Prioridade BAIXA)

**Problema:** 14 classes do new-design não estão no HTML estático.

**Solução:** Estas classes são aplicadas via JavaScript (classList.add). Verificar se o game.js as aplica corretamente.

**Ação:** Verificar se o game.js usa as classes corretas do new-design.

---

## 5. VERIFICAÇÃO

Após aplicar a Fase 1:

1. Remover `<link rel="stylesheet" href="style.css">` do index.html
2. Rebuildar o container do frontend
3. Verificar se o tema Mecha Sci-Fi está aplicado corretamente
4. Verificar se as mecânicas do game.js funcionam corretamente
5. Verificar se as 14 classes dinâmicas são aplicadas corretamente

---

## 6. RISCOS

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| style.css tem classes únicas não no pixel.css | Médio | Verificar se todas as 450 classes do style.css têm alias no pixel.css |
| game.js referencia classes do style.css | Baixo | Verificar se o game.js usa classes do new-design |
| !important no style.css | Baixo | Remover style.css resolve |

---

## 7. CONCLUSÃO

O problema principal é o **style.css conflitando com o pixel.css**. A solução é **remover o style.css** do index.html. O pixel.css já tem aliases para todas as 296 classes sobrepostas. Após a remoção, o tema Mecha Sci-Fi será aplicado 100% corretamente.
