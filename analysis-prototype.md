# Análise do Protótipo — Mempool Miner

**Arquivo:** `prototype-pixel-final.html` (1.270 linhas, ~66 KB)
**Data:** 2026-08-17

---

## 1. ARQUITETURA ATUAL

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TOP BAR (52px):  OPERATOR | WALLET | BLOCK | COMBO | RIG              │
│  XP BAR (4px)                                                                                │
├──────────────┬──────────────────────────────┬──────────────────────────┤
│  COL-LEFT    │      COL-CENTER              │    COL-RIGHT             │
│  (220-280px) │      (flex: 1)               │    (260-340px)           │
│              │                              │                          │
│  MEMPOOL     │  ┌─ RACE BAR ───────────┐   │  ┌─ TABS ─────────────┐  │
│  TX List     │  │ Progress bar         │   │  SHOP│RANK│CARDS│MAIS │  │
│  (desktop)   │  ├──────────────────────┤   │  └────────────────────┘  │
│              │  │                      │   │                          │
│              │  │   WORD GRID          │   │  ┌─ SHOP ────────────┐   │
│              │  │   (12x12 / 8x8 /    │   │  │ 6 store cards      │   │
│              │  │    15x15)            │   │  └───────────────────┘   │
│              │  │                      │   │  ┌─ RANK ───────────┐   │
│              │  │   [SVG overlay]      │   │  │ Leaderboard       │   │
│              │  │   [loading overlay]  │   │  │ Pool ranking      │   │
│              │  │                      │   │  │ Boss block HP     │   │
│              │  └──────────────────────┘   │  └───────────────────┘   │
│              │                              │  ┌─ CARDS ──────────┐   │
│              │                              │  │ Block cards grid  │   │
│              │                              │  │ Season pass track │   │
│              │                              │  └───────────────────┘   │
│              │                              │  ┌─ MAIS ───────────┐   │
│              │                              │  │ 7 SUB-TABS:      │   │
│              │                              │  │ PvP│Sprint│Friends│   │
│              │                              │  │ Staking│Skills│Chat│   │
│              │                              │  │ Market              │   │
│              │                              │  └───────────────────┘   │
├──────────────┴──────────────────────────────┴──────────────────────────┤
│  MOBILE NAV (52px):  GRID │ SHOP │ RANK │ CARDS │ MAIS                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. PROBLEMAS IDENTIFICADOS

### 2.1 Layout

| # | Problema | Gravidade | Onde |
|---|----------|-----------|------|
| L1 | **Coluna esquerda desaparece em ≤1024px sem alternativa** — A lista de transações (mempool) é o feed principal de palavras a encontrar. Em tablet ela simplesmente some (`display: none`), e o jogador não sabe o que procurar. | 🔴 Crítico | `.col-left` @ ≤1024px |
| L2 | **Grid quadrado com `aspect-ratio: 1/1`** — Em telas ultrawide (21:9) o grid fica pequeno demais; em telas verticais (9:16) fica enorme e corta conteúdo. O `min(72vh, 88vw, 760px)` não cobre todos os casos. | 🟡 Médio | `.grid-frame` |
| L3 | **Top bar com 5 stats em 52px fixos** — Em mobile os labels "OPERATOR", "COLD WALLET", "BLOCK", "COMBO", "RIG" com valores longos (ex: `#840,123`) transbordam. O `clamp(12px, 2vw, 32px)` gap não previne overflow. | 🟡 Médio | `.top-bar` |
| L4 | **Drawer mobile cobre 100% da tela** — Em ≤768px, `.col-right` é `position: fixed; inset: 52px 0 52px 0` e sobe com `translateY`. Cobre o grid inteiro, forçando o jogador a fechar o drawer para voltar a jogar. | 🟡 Médio | `.col-right` @ ≤768px |
| L5 | **Sem breakpoint para 42" / TV** — O layout assume máximo ~1920px. Em 42" (3840px) os painéis ficam minúsculos e o grid perde legibilidade. | 🟠 Alto | Global |
| L6 | **Sem breakpoint intermediário (tablet landscape ~820px)** — O salto de 1024px (3 colunas) para 768px (1 coluna) é brusco. Tablets em landscape (820-1024px) perdem a coluna esquerda sem ganhar nada. | 🟡 Médio | @media gaps |
| L7 | **Coluna direita fixa em 260-340px** — O `clamp(260px, 18vw, 340px)` consome até 18% da largura em telas grandes, roubando espaço do grid central. | 🟢 Baixo | `.col-right` |

### 2.2 Navegação

| # | Problema | Gravidade | Onde |
|---|----------|-----------|------|
| N1 | **"MAIS" é um lixão de 7 features** — PvP, Sprint, Friends, Staking, Skills, Chat, Market estão todos empilhados em sub-tabs dentro de um único tab "MAIS". O usuário precisa de 2 cliques para acessar qualquer uma dessas 7 funcionalidades. | 🔴 Crítico | `#tab-mais` |
| N2 | **SHOP e MARKET duplicam funcionalidade** — SHOP vende itens (hints, hardware, Lightning). MARKET também vende itens (HINT_PACK, TIME_FREEZE). O jogador não sabe onde comprar o quê. | 🔴 Crítico | `#tab-shop` vs `#sub-market` |
| N3 | **Sem acesso à lista de transações em mobile/tablet** — A sidebar esquerda some e não há equivalente no mobile nav. O jogador joga cego. | 🔴 Crítico | `.col-left` + `.mobile-nav` |
| N4 | **Botão "GRID" no mobile não faz nada útil** — `setMobileView('grid')` apenas fecha o drawer. Não é uma "view", é "voltar ao jogo". O nome é confuso. | 🟡 Médio | `.mobile-nav` |
| N5 | **RANK mistura 3 conceitos diferentes** — Leaderboard individual, ranking de pools, e Boss Block HP estão no mesmo painel sem separação clara. | 🟡 Médio | `#tab-rank` |
| N6 | **CARDS é orfão** — Block Cards e Season Pass não têm relação clara com o jogo principal. O jogador não entende o propósito. | 🟢 Baixo | `#tab-cards` |
| N7 | **7 sub-tabs em "MAIS" não cabem em mobile** — Em drawer mobile (largura total da tela), as 7 sub-tabs ficam apertadas com `font-size: 6px`. | 🟡 Médio | `.sub-tabs` @ ≤768px |

### 2.3 Organização de Informações

| # | Problema | Gravidade |
|---|----------|-----------|
| I1 | **Hierarquia plana demais** — SHOP, RANK, CARDS, MAIS têm o mesmo peso visual, mas SHOP é usado 10x mais que CARDS. Não há priorização. | 🟡 Médio |
| I2 | **Informações de jogo vs. informações sociais misturadas** — PvP, Friends, Chat (social) estão no mesmo nível que Staking, Skills (progressão) e Market (economia). | 🟡 Médio |
| I3 | **Stats do HUD não refletem estado do jogo** — "COMBO" e "RIG" são dinâmicos mas "BLOCK" é estático no HUD. "COLD WALLET" é o saldo mas o label é confuso para iniciantes. | 🟢 Baixo |
| I4 | **Sem indicador de energia/recursos** — O SHOP vende "ENERGIA" mas não há display de energia atual no HUD. O jogador não sabe quantas cargas tem. | 🟡 Médio |
| I5 | **Boss Block escondido em RANK** — O Boss Block é um evento de jogo urgente, mas está escondido dentro da aba de ranking. | 🟡 Médio |

---

## 3. SUGESTÕES DE MELHORIA

### 3.1 Nova Arquitetura de Navegação

```
MENU PRINCIPAL (5 itens, peso igual):

  🎮 JOGO       → Grid + Mempool TX list + Race bar
  ⚡ UPGRADES   → Shop (hints, hardware, Lightning, energia, crates)
  🏆 COMPETIR   → Leaderboard + Pool ranking + PvP + Sprint + Boss Block
  👤 PERFIL     → Cards + Season Pass + Skills + Staking
  👥 SOCIAL     → Friends + Chat + Market
```

**Mudanças:**
- Eliminar o tab "MAIS" — distribuir suas 7 sub-tabs nos 4 novos grupos
- Unificar SHOP e MARKET em "UPGRADES"
- Mover Boss Block para "COMPETIR" (é um evento competitivo)
- Mover PvP e Sprint para "COMPETIR"
- Mover Skills e Staking para "PERFIL"
- Mover Friends e Chat para "SOCIAL"

### 3.2 Layout por Breakpoint

#### 📱 Mobile (≤480px)

```
┌─────────────────────────┐
│  HUD COMPACTO            │
│  ⚡12,340  #840K  1.0x  │
├─────────────────────────┤
│                         │
│    WORD GRID            │
│    (max 92vw)           │
│                         │
├─────────────────────────┤
│  TX QUEUE (scroll-h)    │
│  [BLOCK] [HASH] [NODE]  │
├─────────────────────────┤
│ 🎮 ⚡ 🏆 👤 👥          │
└─────────────────────────┘
```

- **Grid central** com `max-width: 92vw`
- **TX Queue horizontal scrollável** abaixo do grid (substitui coluna esquerda)
- **Bottom nav** com 5 ícones (sem texto, só ícones para economizar espaço)
- **Painéis secundários** abrem como modal bottom-sheet (50% altura) em vez de drawer full-screen
- **HUD compacto**: só mostra saldo, block e combo (remove operator name e rig)

#### 📱 Mobile Landscape (≤640px altura)

```
┌──────────────────────────────────────┐
│  HUD: ⚡12,340  #840K  1.0x         │
├──────────────┬───────────────────────┤
│  TX QUEUE    │   WORD GRID           │
│  (vertical)  │   (quadrado)          │
│              │                       │
├──────────────┴───────────────────────┤
│  🎮 ⚡ 🏆 👤 👥                      │
└──────────────────────────────────────┘
```

- **2 colunas**: TX queue à esquerda (estreita) + grid à direita
- **Bottom nav** mantida

#### 📟 Tablet Portrait (481-768px)

```
┌──────────────────────────────────────┐
│  HUD: [NAME] ⚡12,340  #840K  1.0x  │
├──────────────────────────────────────┤
│  TX QUEUE (scroll-h)                 │
├──────────────────────────────────────┤
│                                      │
│         WORD GRID                    │
│         (max 60vh)                   │
│                                      │
├──────────────────────────────────────┤
│  🎮 ⚡ 🏆 👤 👥                      │
└──────────────────────────────────────┘
```

- **TX Queue** como barra horizontal scrollável acima do grid
- **Grid** com `max-height: 60vh` para caber com TX queue
- **Bottom nav** com ícones + labels

#### 💻 Tablet Landscape (769-1024px)

```
┌──────────────────────────────────────────────────┐
│  HUD: [NAME] ⚡12,340  #840K  1.0x  CPU         │
├──────────────┬───────────────────┬───────────────┤
│  TX QUEUE    │   WORD GRID       │  PANEL (tabs) │
│  (col-left)  │   (flex: 1)       │  (280px)      │
│              │                   │               │
│  [BLOCK]     │                   │  SHOP/RANK/   │
│  [HASH]     │                   │  CARDS/...    │
│  [NODE]     │                   │               │
│  ...        │                   │               │
└──────────────┴───────────────────┴───────────────┘
```

- **3 colunas restauradas** — coluna esquerda volta com TX queue
- **Coluna direita** com tabs (nova estrutura de 5 tabs)
- **Grid** flexível no centro

#### 🖥️ Notebook/Desktop (1025-1920px)

```
┌─────────────────────────────────────────────────────────────┐
│  HUD: [NAME] ⚡12,340  #840K  1.0x  CPU  ⚡E: 3/5  🟢ON    │
├──────────────┬──────────────────────────┬───────────────────┤
│  TX QUEUE    │                          │  PANEL            │
│  (280px)     │      WORD GRID           │  (320px)          │
│              │      (max 760px)         │                   │
│  [BLOCK]     │                          │  ┌─ TABS ───────┐ │
│  [HASH]     │                          │  🎮⚡🏆👤👥     │ │
│  [NODE]     │                          │  └──────────────┘ │
│  [CRYPTO]   │                          │                   │
│  [GENESIS]  │                          │  [conteúdo do     │
│  [LEDGER]   │                          │   tab ativo]      │
│             │                          │                   │
└──────────────┴──────────────────────────┴───────────────────┘
```

- **3 colunas** com larguras otimizadas
- **HUD completo** com todos os stats + energia + status
- **Grid** centralizado com `max-width: 760px`
- **Painel direito** com 5 tabs na nova estrutura

#### 📺 42" TV (1921-3840px)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  HUD: [NAME]  ⚡12,340  #840K  1.0x  CPU  ⚡E: 3/5  🟢ON              │
├──────────────┬──────────────────────────────────┬───────────────────────┤
│  TX QUEUE    │                                  │  PANEL                │
│  (380px)     │        WORD GRID                 │  (420px)              │
│              │        (max 1200px)              │                       │
│  [BLOCK]     │                                  │  ┌─ TABS ──────────┐  │
│  [HASH]     │                                  │  🎮⚡🏆👤👥        │  │
│  [NODE]     │                                  │  └────────────────┘  │
│  [CRYPTO]   │                                  │                       │
│  [GENESIS]  │                                  │  [conteúdo do        │
│  [LEDGER]   │                                  │   tab ativo]         │
│             │                                  │                       │
│  ────────── │                                  │  ──────────────────   │
│  [PROOF]    │                                  │  [quick actions]     │
│  [REWARD]   │                                  │                       │
└──────────────┴──────────────────────────────────┴───────────────────────┘
```

- **Fontes escaladas**: `font-size` mínimo aumentado 50% (`clamp` com base maior)
- **Grid maior**: `max-width: 1200px` para legibilidade à distância
- **Colunas mais largas**: esquerda 380px, direita 420px
- **Controles maiores**: botões com `padding` aumentado para uso com controle remoto
- **Novo breakpoint**: `@media (min-width: 1921px)`

### 3.3 Menu Sugerido

```
┌─────────────────────────────────────────────────────────┐
│  NAVEGAÇÃO PRINCIPAL (5 tabs, peso visual igual)        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🎮 JOGO                                                │
│  ── (padrão, sempre visível no grid)                    │
│  • Mempool TX Queue (lista de palavras)                 │
│  • Race Bar (timer da rede)                             │
│  • Word Grid (campo de jogo)                            │
│                                                         │
│  ⚡ UPGRADES                                            │
│  ── (unifica SHOP + MARKET)                             │
│  • Decrypt Hint — 5K SATS                              │
│  • Time Freeze — 10K SATS                              │
│  • ASIC Rig Upgrade — 100K+ SATS                       │
│  • Lightning L2 — 1M SATS                              │
│  • Energia — 2K SATS                                   │
│  • Mempool Crate — GRATIS / 5K                         │
│  • Market (itens da comunidade)                         │
│                                                         │
│  🏆 COMPETIR                                            │
│  ── (unifica RANK + PvP + Sprint + Boss)               │
│  • Top Miners (leaderboard individual)                  │
│  • Top Pools (ranking de pools)                        │
│  • Boss Block (HP + countdown)                         │
│  • PvP Arena (desafiar jogador)                        │
│  • Sprint (timer challenge)                            │
│                                                         │
│  👤 PERFIL                                              │
│  ── (unifica CARDS + Skills + Staking)                 │
│  • Block Cards (coleção)                               │
│  • Season Pass (progressão)                            │
│  • Skill Tree (habilidades)                            │
│  • Staking (APY + saldo)                               │
│                                                         │
│  👥 SOCIAL                                              │
│  ── (unifica Friends + Chat)                           │
│  • Friends (lista + status online)                     │
│  • Chat (mensagens globais)                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.4 Organização de Informações Sugerida

#### HUD (Top Bar) — Prioridade de informações

| Posição | Info | Por quê |
|---------|------|---------|
| Esquerda | **Saldo (⚡ SATS)** | Métrica #1 do jogador |
| Centro-Esq | **Block #** | Contexto do jogo |
| Centro-Dir | **Combo** | Feedback de performance |
| Direita | **Energia** | Recurso crítico (faltando hoje) |
| Extrema Dir | **Rig + Status** | Hardware + Lightning mode indicator |

#### Painel Direito — Sub-navegação por tab

Cada tab usa **seções** em vez de sub-tabs:

**⚡ UPGRADES:**
```
┌─ POWER-UPS ──────────────────┐
│ Decrypt Hint     5K SATS     │
│ Time Freeze      10K SATS    │
│ Energia            2K SATS   │
├─ HARDWARE ───────────────────┤
│ ASIC Rig V1      100K SATS  │
│ Lightning L2     1M SATS    │
├─ LOOT ───────────────────────┤
│ Mempool Crate    FREE / 5K  │
└──────────────────────────────┘
```

**🏆 COMPETIR:**
```
┌─ BOSS BLOCK ─────────────────┐
│ MEV_WHALE    HP: 65% ██████  │
│ Próximo em 3 blocos          │
├─ TOP MINERS ─────────────────┤
│ #1 HalFinney    8,200,000    │
│ #2 AdamBack     4,100,000    │
│ #3 [VOCÊ]        12,340      │
├─ TOP POOLS ──────────────────┤
│ #1 [AntPool]    15,000,000  │
├─ ARENA ──────────────────────┤
│ [BUSCAR OPOSITOR]            │
│ [INICIAR SPRINT]  04:22     │
└──────────────────────────────┘
```

---

## 4. RESUMO DAS AÇÕES PRIORITÁRIAS

| Prioridade | Ação | Impacto |
|------------|------|---------|
| 🔴 P0 | Mover TX Queue para mobile/tablet (scroll horizontal abaixo do grid) | Jogador precisa ver as palavras |
| 🔴 P0 | Eliminar tab "MAIS" — redistribuir 7 features em 4 categorias lógicas | Navegação clara |
| 🔴 P0 | Unificar SHOP + MARKET em "UPGRADES" | Fim da duplicação |
| 🟠 P1 | Adicionar display de Energia no HUD | Recurso invisível hoje |
| 🟠 P1 | Adicionar breakpoint para 42" (≥1921px) | Suporte a TV |
| 🟠 P1 | Mover Boss Block para tab "COMPETIR" | Evento urgente visível |
| 🟡 P2 | Reduzir drawer mobile para bottom-sheet (50% altura) | Grid visível durante navegação |
| 🟡 P2 | Adicionar breakpoint tablet landscape (769-1024px) | Transição suave |
| 🟡 P2 | Renomear botão "GRID" para "JOGO" ou "⬅️" no mobile | Clareza |
| 🟢 P3 | Adicionar seções visuais dentro de cada tab | Hierarquia de info |

---

## 5. CSS BREAKPOINTS SUGERIDOS

```css
/* Mobile portrait */
@media (max-width: 480px) {
  /* 1 coluna, grid central, TX queue scroll-h, bottom nav ícones */
}

/* Mobile landscape */
@media (max-height: 640px) and (orientation: landscape) {
  /* 2 colunas: TX queue estreita + grid */
}

/* Tablet portrait */
@media (min-width: 481px) and (max-width: 768px) {
  /* 1 coluna, TX queue scroll-h, bottom nav ícones+labels */
}

/* Tablet landscape */
@media (min-width: 769px) and (max-width: 1024px) {
  /* 3 colunas restauradas */
}

/* Notebook / Desktop */
@media (min-width: 1025px) and (max-width: 1920px) {
  /* 3 colunas otimizadas, HUD completo */
}

/* 42" TV / Large screen */
@media (min-width: 1921px) {
  /* Fontes +50%, grid 1200px, colunas mais largas */
}
```
