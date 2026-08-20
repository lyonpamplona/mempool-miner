# Audit CSS — Mempool Miner Frontend

> Arquivo: `frontend/style.css` (4198 linhas, 95KB)
> Data: 2026-08-16

## Resumo Executivo

| Categoria | Critico | Medio | Baixo | Total |
|-----------|---------|-------|-------|-------|
| 1. Classes nao usadas | 0 | 0 | 35 | 35 |
| 2. Variaveis CSS nao definidas | 0 | 4 | 0 | 4 |
| 3. Media queries faltando | 0 | 8 | 0 | 8 |
| 4. Overflow nao tratado | 0 | 0 | 1 | 1 |
| 5. Unidades fixas (px) | 0 | 0 | 79 | 79 |
| 6. Z-index conflicts | 2 | 3 | 0 | 5 |
| 7. Animacoes sem reduced-motion | 0 | 0 | 0 | 0 |
| 8. Cores hardcoded | 0 | 0 | 28 | 28 |
| 9. Estilos duplicados | 0 | 0 | 0 | 0 |
| 10. Layouts quebrados mobile | 0 | 3 | 0 | 3 |
| 11. Painéis sem espacamento | 0 | 0 | 0 | 0 |
| 12. Fontes sem fallback | 0 | 2 | 5 | 7 |
| SINTAXE | 1 | 0 | 0 | 1 |
| **TOTAL** | **3** | **20** | **152** | **175** |

---

## 1. Classes CSS definidas mas nunca usadas no HTML/JS

**Impacto: BAIXO** — 35 classes definidas sem uso detectavel.

| Linha | Classe | Observacao |
|-------|--------|------------|
| 929 | `.achievement-card` | Sem uso no HTML nem no JS detectado |
| 901 | `.achievements-filter-btn` | Sem uso no HTML nem no JS detectado |
| 2855 | `.block-card` | Sem uso no HTML nem no JS detectado |
| 2106 | `.btn-skill-upgrade` | Sem uso no HTML nem no JS detectado |
| 2969 | `.card-pull-card` | Sem uso no HTML nem no JS detectado |
| 4069 | `.crate-particle` | Sem uso no HTML nem no JS detectado |
| 4011 | `.crate-result-rarity` | Sem uso no HTML nem no JS detectado |
| 420 | `.cross-line` | Sem uso no HTML nem no JS detectado |
| 2535 | `.energy-depleted-overlay` | Sem uso no HTML nem no JS detectado |
| 3784 | `.friend-item` | Sem uso no HTML nem no JS detectado |
| 3259 | `.market-history-type` | Sem uso no HTML nem no JS detectado |
| 3214 | `.market-sell-btn` | Sem uso no HTML nem no JS detectado |
| 3190 | `.market-sell-form` | Sem uso no HTML nem no JS detectado |
| 3205 | `.market-sell-input` | Sem uso no HTML nem no JS detectado |
| 3196 | `.market-sell-select` | Sem uso no HTML nem no JS detectado |
| 1307 | `.mission-type-badge` | Sem uso no HTML nem no JS detectado |
| 293 | `.rank-item` | Sem uso no HTML nem no JS detectado |
| 4020 | `.rarity-common` | Sem uso no HTML nem no JS detectado |
| 4035 | `.rarity-epic` | Sem uso no HTML nem no JS detectado |
| 4040 | `.rarity-legendary` | Sem uso no HTML nem no JS detectado |
| 4030 | `.rarity-rare` | Sem uso no HTML nem no JS detectado |
| 4025 | `.rarity-uncommon` | Sem uso no HTML nem no JS detectado |
| 1941 | `.skill-branch-header` | Sem uso no HTML nem no JS detectado |
| 1947 | `.skill-branch-icon` | Sem uso no HTML nem no JS detectado |
| 1959 | `.skill-branch-level` | Sem uso no HTML nem no JS detectado |
| 1952 | `.skill-branch-name` | Sem uso no HTML nem no JS detectado |
| 2046 | `.skill-node-tooltip` | Sem uso no HTML nem no JS detectado |
| 2096 | `.skill-tooltip-cost` | Sem uso no HTML nem no JS detectado |
| 2090 | `.skill-tooltip-desc` | Sem uso no HTML nem no JS detectado |
| 2083 | `.skill-tooltip-title` | Sem uso no HTML nem no JS detectado |
| 3653 | `.sprint-leaderboard-list` | Sem uso no HTML nem no JS detectado |
| 3649 | `.sprint-leaderboard-panel` | Sem uso no HTML nem no JS detectado |
| 1856 | `.staking-bonus-indicator` | Sem uso no HTML nem no JS detectado |
| 1817 | `.staking-history-item` | Sem uso no HTML nem no JS detectado |
| 366 | `.word-fee` | Sem uso no HTML nem no JS detectado |

**Sugestao:** Remover classes nao usadas para reduzir o tamanho do CSS. Algumas podem ser usadas dinamicamente via JS (verificar `classList.add` no game.js).

---

## 2. Variaveis CSS usadas mas nao definidas no :root

**Impacto: MEDIO** — 4 variaveis referenciadas sem definicao.

| Linha | Variavel | Onde usada |
|-------|----------|------------|
| 434 | `--cell-size` | `width: var(--cell-size);` |
| 426 | `--grid-gap` | `gap: var(--grid-gap);` |
| 4091 | `--tx` | `transform: translate(var(--tx), var(--ty)) scale(0);` |
| 4091 | `--ty` | `transform: translate(var(--tx), var(--ty)) scale(0);` |

**Sugestao:** Adicionar as variaveis ao `:root` ou substituir por valores diretos.

---

## 3. Media queries faltando para responsividade

**Impacto: MEDIO** — 9 paineis sem adaptacao para telas pequenas.

| Painel | Problema |
|--------|----------|
| `.staking-panel` | Sem media query max-width para telas < 768px |
| `.skills-panel` | Sem media query max-width para telas < 768px |
| `.missions-panel` | Sem media query max-width para telas < 768px |
| `.market-panel` | Sem media query max-width para telas < 768px |
| `.season-panel` | Sem media query max-width para telas < 768px |
| `.cards-panel` | Sem media query max-width para telas < 768px |
| `.pvp-panel` | Sem media query max-width para telas < 768px |

**Sugestao:** Adicionar `@media (max-width: 768px)` para cada painel com:
- `max-height` reduzido
- `overflow-y: auto` para scroll interno
- Ajustes de padding/gap para telas estreitas

---

## 4. Elementos com overflow nao tratado

**Impacto: BAIXO** — 1 elemento com risco de overflow.

| Linha | Elemento | Problema |
|-------|----------|----------|
| 365 | `.word-text` | Texto sem `overflow-wrap` ou `word-break` para palavras longas |

**Sugestao:** Adicionar `overflow-wrap: anywhere` a `.word-text` para evitar que palavras BIP39 longas quebrem o layout.

---

## 5. Unidades fixas (px) que deveriam ser relativas

**Impacto: BAIXO** — 79 ocorrencias de valores fixos em px.

### Font-size em px (principais)

| Linha | Valor | Problema |
|-------|-------|----------|
| 191 | `10px` | `font-size: 10px;` |
| 223 | `10px` | `.node-status { color: var(--text-muted); font-size: 10px; te` |
| 366 | `8px` | `.word-fee { flex: 0 0 auto; padding: 2px 4px; border-radius:` |
| 459 | `10px` | `font-size: 10px;` |
| 751 | `10px` | `font-size: 10px;` |
| 781 | `9px` | `font-size: 9px;` |
| 958 | `28px` | `font-size: 28px;` |
| 998 | `9px` | `font-size: 9px;` |
| 1034 | `10px` | `font-size: 10px;` |
| 1069 | `32px` | `font-size: 32px;` |
| 1240 | `10px` | `font-size: 10px;` |
| 1271 | `10px` | `font-size: 10px;` |
| 1311 | `9px` | `font-size: 9px;` |
| 1338 | `10px` | `font-size: 10px;` |
| 1432 | `10px` | `font-size: 10px;` |
| 1445 | `10px` | `font-size: 10px;` |
| 1452 | `9px` | `font-size: 9px;` |
| 1547 | `9px` | `font-size: 9px;` |
| 1622 | `10px` | `font-size: 10px;` |
| 1701 | `10px` | `font-size: 10px;` |

### Dimensoes fixas grandes

| Linha | Valor | Contexto |
|-------|-------|----------|
| 156 | `560px` | `max-width: 560px;` |
| 608 | `560px` | `@media (min-width: 560px) {` |
| 618 | `761px` | `@media (min-width: 761px) {` |
| 629 | `470px` | `.grid-wrapper { min-height: 470px; padding: 18px; }` |
| 634 | `1181px` | `@media (min-width: 1181px) {` |
| 636 | `620px` | `.main-layout { grid-template-columns: 260px minmax(0, 1fr) 2` |
| 1128 | `560px` | `@media (min-width: 560px) {` |
| 1354 | `560px` | `@media (min-width: 560px) {` |
| 1356 | `600px` | `max-height: 600px;` |
| 1361 | `761px` | `@media (min-width: 761px) {` |
| 1363 | `700px` | `max-height: 700px;` |
| 1368 | `1181px` | `@media (min-width: 1181px) {` |
| 1370 | `750px` | `max-height: 750px;` |
| 1407 | `400px` | `max-height: 400px;` |
| 1561 | `559px` | `@media (max-width: 559px) {` |
| 1575 | `761px` | `@media (min-width: 761px) {` |
| 1577 | `600px` | `max-height: 600px;` |
| 1581 | `1181px` | `@media (min-width: 1181px) {` |
| 1583 | `650px` | `max-height: 650px;` |
| 2145 | `560px` | `@media (min-width: 560px) {` |
| 2147 | `600px` | `max-height: 600px;` |
| 2152 | `761px` | `@media (min-width: 761px) {` |
| 2154 | `700px` | `max-height: 700px;` |
| 2159 | `1181px` | `@media (min-width: 1181px) {` |
| 2161 | `750px` | `max-height: 750px;` |
| 2851 | `500px` | `max-height: 500px;` |
| 3483 | `768px` | `@media (max-width: 768px) {` |
| 3585 | `400px` | `max-width: 400px;` |
| 3692 | `768px` | `@media (max-width: 768px) {` |
| 3780 | `400px` | `max-height: 400px;` |
| 3863 | `768px` | `@media (max-width: 768px) {` |
| 3963 | `400px` | `max-width: 400px;` |
| 4097 | `768px` | `@media (max-width: 768px) {` |
| 4186 | `768px` | `@media (max-width: 768px) {` |

**Sugestao:**
- `font-size`: usar `clamp(min, preferred, max)` ou `rem` para escalabilidade
- `min-height/max-height`: usar `vh` ou `dvh` para adaptacao a viewport
- `width/height` grandes: usar `%` ou `vw`/`vh`

---

## 6. Z-index conflicts ou valores muito altos

**Impacto: CRITICO/MEDIO** — Escala de z-index inconsistente.

| Linha | Seletor | z-index | Impacto |
|-------|---------|---------|---------|
| 3954 | `.crate-modal-overlay {` | `10000` | CRITICO |
| 2961 | `.card-pull-overlay {` | `9999` | CRITICO |
| 3540 | `.sprint-timer-container {` | `9999` | CRITICO |
| 3571 | `.sprint-result-overlay {` | `9999` | CRITICO |
| 3294 | `.global-event-banner {` | `9998` | MEDIO |

### Escala atual de z-index:

| Valor | Seletor | Uso |
|-------|---------|-----|
| `10000` | `.crate-modal-overlay {` | |
| `9999` | `.card-pull-overlay {` | |
| `9999` | `.sprint-timer-container {` | |
| `9999` | `.sprint-result-overlay {` | |
| `9998` | `.global-event-banner {` | |
| `300` | `.skip-link {` | |
| `250` | `.achievement-toast {` | |
| `200` | `.modal-overlay {` | |
| `180` | `.update-banner {` | |
| `170` | `.floating-text {` | |
| `160` | `.mobile-nav {` | |
| `155` | `.btn-decoder-launch {` | |
| `50` | `` | |
| `25` | `.boss-hud {` | |
| `25` | `.energy-depleted-overlay {` | |
| `20` | `.grid-overlay {` | |
| `10` | `.svg-lines {` | |
| `10` | `.achievement-tooltip {` | |
| `7` | `.cell:focus-visible { position: relative; z-index: 7; outline: 3px solid var(--hint-yellow); outline-offset: 1px; color: var(--text-main); }` | |
| `5` | `.cell.selected { z-index: 5; transform: scale(1.08); border-color: var(--btc-orange); background: rgba(247, 147, 26, 0.22); color: var(--btc-orange); box-shadow: 0 0 12px rgba(247, 147, 26, 0.3); contain: strict; /* Fase 1: previne overflow do scale */ }` | |
| `1` | `.race-bar-network {` | |

**Sugestao:** Padronizar escala de z-index:
```
10   - overlays internos (grid-overlay, boss-hud)
20   - tooltips
50   - floating elements
100  - modais
150  - banners fixos
200  - overlays de tela cheia
```
Remover valores >= 9999 e substituir por maximo de 200.

---

## 7. Animacoes sem prefers-reduced-motion

**Impacto: OK** — O CSS possui regra global `@media (prefers-reduced-motion: reduce)` na linha 651 que cobre todos os elementos com `*, *::before, *::after`.

### Animacoes detectadas (33 total):

| Linha | @keyframes |
|-------|------------|
| 361 | `pulse` |
| 409 | `spin` |
| 453 | `pulseHint` |
| 561 | `floatScore` |
| 673 | `slashingFlash` |
| 683 | `halvingFlash` |
| 693 | `rbfPulse` |
| 737 | `bossIconPulse` |
| 788 | `bossFlash` |
| 798 | `bossShake` |
| 830 | `bossDefeatPulse` |
| 849 | `bossHpDamage` |
| 1074 | `achievementBounce` |
| 1423 | `chatMessageIn` |
| 2016 | `skillNodePulse` |
| 2134 | `skillUnlock` |
| 2254 | `decoderTimerPulse` |
| 2341 | `decoderFeedbackIn` |
| 2409 | `decoderLaunchPulse` |
| 2422 | `decoderReward` |
| 2894 | `legendary-glow` |
| 3023 | `card-pull-fade-in` |
| 3028 | `card-pull-bounce` |
| 3326 | `event-icon-pulse` |
| 3477 | `lightning-grid-flash` |
| 3553 | `sprint-timer-pulse` |
| 3637 | `sprint-result-fade-in` |
| 3642 | `sprint-result-bounce` |
| 3969 | `crateReveal` |
| 3983 | `crateShake` |
| 4046 | `legendaryGlow` |
| 4085 | `particleBurst` |
| 4174 | `levelUpPulse` |

### Cobertura reduced-motion especifica:

| Animacao | Cobertura |
|----------|-----------|
| `.achievement-toast` | Sim (bloco especifico) |
| `.mission-progress-fill` | Sim (bloco especifico) |
| `.chat-message` | Sim (bloco especifico) |
| `.staking-countdown-value` | Sim (bloco especifico) |
| `.skill-node` | Sim (bloco especifico) |
| `.available` | Sim (bloco especifico) |
| `.decoder-timer-bar` | Sim (bloco especifico) |
| `.urgent` | Sim (bloco especifico) |

**Observacao:** A regra global na linha 651 (`*, *::before, *::after`) cobre todas as animacoes. Bloques especificos existem para: achievements, missions, chat, staking, skills, decoder.

---

## 8. Cores hardcoded (nao usando variaveis CSS)

**Impacto: BAIXO** — 28 cores hardcoded que poderiam ser variaveis.

| Linha | Cor | Contexto |
|-------|-----|----------|
| 27 | `#0ea5e9` | `--btc-orange: #0ea5e9;` |
| 28 | `#020617` | `--bg-dark: #020617;` |
| 140 | `#fecaca` | `.connectivity-pill.offline { color: #fecaca; border-color: r` |
| 309 | `#94a3b8` | `.rank-item.top-2 { border-color: #94a3b8; }` |
| 310 | `#b45309` | `.rank-item.top-3 { border-color: #b45309; }` |
| 770 | `#ff6b6b` | `background: linear-gradient(90deg, var(--error-red), #ff6b6b` |
| 2605 | `#ffd700` | `background: linear-gradient(90deg, var(--btc-orange), #ffd70` |
| 2628 | `#ffd700` | `background: linear-gradient(135deg, var(--btc-orange), #ffd7` |
| 2806 | `#9ca3af` | `.card-filter[data-rarity="common"].active { background: #9ca` |
| 2807 | `#3b82f6` | `.card-filter[data-rarity="rare"].active { background: #3b82f` |
| 2808 | `#8b5cf6` | `.card-filter[data-rarity="epic"].active { background: #8b5cf` |
| 2809 | `#f59e0b` | `.card-filter[data-rarity="legendary"].active { background: #` |
| 2874 | `#374151` | `background: linear-gradient(135deg, #374151, #4b5563);` |
| 2874 | `#4b5563` | `background: linear-gradient(135deg, #374151, #4b5563);` |
| 2875 | `#6b7280` | `border: 1px solid #6b7280;` |
| 2879 | `#1e3a5f` | `background: linear-gradient(135deg, #1e3a5f, #2563eb);` |
| 2879 | `#2563eb` | `background: linear-gradient(135deg, #1e3a5f, #2563eb);` |
| 2880 | `#3b82f6` | `border: 1px solid #3b82f6;` |
| 2884 | `#4c1d95` | `background: linear-gradient(135deg, #4c1d95, #7c3aed);` |
| 2884 | `#7c3aed` | `background: linear-gradient(135deg, #4c1d95, #7c3aed);` |
| 2885 | `#8b5cf6` | `border: 1px solid #8b5cf6;` |
| 2889 | `#78350f` | `background: linear-gradient(135deg, #78350f, #f59e0b);` |
| 2889 | `#f59e0b` | `background: linear-gradient(135deg, #78350f, #f59e0b);` |
| 2890 | `#fbbf24` | `border: 1px solid #fbbf24;` |
| 2910 | `#9ca3af` | `.block-card.common .block-card-rarity { color: #9ca3af; }` |
| 2911 | `#60a5fa` | `.block-card.rare .block-card-rarity { color: #60a5fa; }` |
| 2912 | `#a78bfa` | `.block-card.epic .block-card-rarity { color: #a78bfa; }` |
| 2913 | `#fbbf24` | `.block-card.legendary .block-card-rarity { color: #fbbf24; }` |
| 2983 | `#6b7280` | `border: 2px solid #6b7280;` |
| 2988 | `#3b82f6` | `border: 2px solid #3b82f6;` |
| 2993 | `#8b5cf6` | `border: 2px solid #8b5cf6;` |
| 2998 | `#fbbf24` | `border: 2px solid #fbbf24;` |
| 3385 | `#a855f7` | `border-bottom-color: #a855f7;` |
| 3390 | `#a855f7` | `color: #a855f7;` |
| 3399 | `#eab308` | `border-bottom-color: #eab308;` |
| 3404 | `#eab308` | `color: #eab308;` |
| 3413 | `#f97316` | `border-bottom-color: #f97316;` |
| 3418 | `#f97316` | `color: #f97316;` |
| 3427 | `#0ea5e9` | `border-bottom-color: #0ea5e9;` |
| 3432 | `#0ea5e9` | `color: #0ea5e9;` |
| 3512 | `#ff6b00` | `background: linear-gradient(135deg, var(--btc-orange), #ff6b` |
| 3530 | `#22c55e` | `background: linear-gradient(135deg, #22c55e, #16a34a);` |
| 3530 | `#16a34a` | `background: linear-gradient(135deg, #22c55e, #16a34a);` |
| 3917 | `#22c55e` | `background: #22c55e;` |
| 3934 | `#f59e0b` | `background: #f59e0b;` |
| 4022 | `#9ca3af` | `color: #9ca3af;` |
| 4032 | `#3b82f6` | `color: #3b82f6;` |
| 4156 | `#f59e0b` | `background: linear-gradient(90deg, var(--btc-orange), #f59e0` |

**Sugestao:** Mapear cores recorrentes para variaveis CSS:
- `#ff6b6b` → `--error-red-light`
- `#ffd700` → `--golden-yellow`
- `#9ca3af` → `--gray-400`
- `#3b82f6` → `--blue-500`
- `#8b5cf6` → `--purple-500`
- `#f59e0b` → `--amber-500`

---

## 9. Estilos duplicados ou redundantes

**Impacto: BAIXO** — Sem duplicacoes criticas encontradas.

O CSS segue um padrao de organizacao por fases (Fase 1-11), com seletores redefinidos em media queries diferentes. Isso e intencional e nao constitui duplicacao.

---

## 10. Layouts quebrados em telas pequenas (< 768px)

**Impacto: MEDIO** — 3 grids sem fallback mobile.

| Linha | Grid | Problema |
|-------|------|----------|
| 210 | `grid-template-columns: repeat(2, minmax(0, 1fr));` | Sem override max-width para mobile |
| 289 | `grid-template-columns: repeat(2, minmax(0, 1fr));` | Sem override max-width para mobile |
| 1726 | `grid-template-columns: repeat(3, 1fr);` | Sem override max-width para mobile |

**Sugestao:** Adicionar media queries para colapsar grids:
```css
@media (max-width: 768px) {
    .mining-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .leaderboard-list, .word-bank-list { grid-template-columns: minmax(0, 1fr); }
}
```

---

## 11. Painéis sobrepostos ou sem espacamento adequado

**Impacto: BAIXO** — Layout geral usa `gap` consistentemente.

### Observacoes:
- `.dashboard` usa `gap: 16px` (linha 176)
- `.main-layout` usa `gap: 14px` (linha 260)
- `.game-area` usa `gap: 12px` (linha 349)
- Media queries ajustam gaps para telas maiores (18px, 24px)

**Sugestao:** Verificar visualmente em telas de 360px (mobile pequeno) se os painéis nao se sobrepem devido ao `position: fixed` dos elementos flutuantes (mobile-nav, update-banner, achievement-toast).

---

## 12. Fontes nao declaradas ou fallbacks faltando

**Impacto: MEDIO** — 7 problemas de fonte.

### Font-family sem fallback:

| Linha | Declaracao | Problema |
|-------|------------|----------|
| 59 | `font-family: var(--font-mono);` | Sem fallback generico |
| 514 | `font-family: var(--font-mono);` | Sem fallback generico |
| 1713 | `font-family: var(--font-mono);` | Sem fallback generico |
| 1742 | `font-family: var(--font-mono);` | Sem fallback generico |
| 2199 | `font-family: var(--font-mono);` | Sem fallback generico |
| 2287 | `font-family: var(--font-mono);` | Sem fallback generico |

### Fonte JetBrains Mono nao importada:

| Linha | Problema |
|-------|----------|
| 16 | `--font-mono: 'JetBrains Mono', ...` referenciada mas sem `@import` ou `@font-face` no CSS |

**Sugestao:**
1. Adicionar ao HTML: `<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap" rel="stylesheet">`
2. Ou adicionar ao CSS: `@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap');`
3. Adicionar fallbacks genericos a todas as declaracoes de font-family

---

## SINTAXE: Erro de fechamento de media query

**Impacto: CRITICO**

| Linha | Problema |
|-------|----------|
| 3483 | `@media (max-width: 768px)` para `.global-event-banner-inner` nao tem fechamento `}` antes do comentario da Fase 5 (linha 3506) |

**Evidencia:**
```css
/* Linha 3483 */
@media (max-width: 768px) {
    .global-event-banner-inner { ... }
    .global-event-icon { ... }
    .global-event-label { ... }
    .global-event-description { ... }
    .global-event-countdown { ... }
/* Linha 3505 — falta } aqui */
/* ==========================================================================
   Fase 5: Modo Sprint — Estilos
   ========================================================================== */
```

**Sugestao:** Adicionar `}` na linha 3505 antes do comentario da Fase 5.

---

## Recomendacoes Prioritarias

### CRITICO (corrigir imediatamente)
1. **Sintaxe:** Fechar media query na linha 3505 — quebra todo o CSS subsequente
2. **Z-index:** Reduzir valores >= 9999 (`.card-pull-overlay`, `.sprint-timer-container`, `.sprint-result-overlay`, `.crate-modal-overlay`) para maximo 200

### MEDIO (corrigir proximo sprint)
3. **Variaveis CSS:** Definir 4 variaveis nao declaradas no :root
4. **Responsividade:** Adicionar media queries para 9 paineis sem adaptacao mobile
5. **Layouts mobile:** Colapsar 3 grids em 1 coluna para telas < 768px
6. **Fontes:** Importar JetBrains Mono e adicionar fallbacks

### BAIXO (melhorias incrementais)
7. **Classes nao usadas:** Remover 35 classes mortas do CSS
8. **Cores hardcoded:** Mapear 28 cores para variaveis CSS
9. **Unidades fixas:** Converter 79 valores px para rem/vh/clamp()
10. **Overflow:** Adicionar overflow-wrap a elementos de texto

---

## Metricas Gerais

| Metrica | Valor |
|---------|-------|
| Linhas de CSS | 4198 |
| Tamanho do arquivo | 95KB |
| Classes CSS definidas | 378 |
| Classes usadas | 343 |
| Classes nao usadas | 35 (9.3%) |
| Variaveis CSS no :root | 15 |
| Variaveis CSS usadas | 19 |
| Media queries | 25+ |
| @keyframes | 33 |
| Z-index maximo | 10000 |
| Cores hardcoded unicas | 48 |
