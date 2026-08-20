# Audit HTML — Mempool Miner Frontend

**Arquivo:** `frontend/index.html` (682 linhas)
**Data:** 2026-08-16
**Escopo:** 10 critérios de qualidade estrutural

---

## Resumo Executivo

| Critério | Problemas encontrados | Críticos | Médios | Baixos |
|---|---|---|---|---|
| 1. IDs duplicados | 0 | — | — | — |
| 2. Classes sem CSS | 43 | 1 | 1 | 0 |
| 3. IDs sem JS | 53 | 2 | 3 | 0 |
| 4. ARIA faltando | 3 | — | 1 | 0 |
| 5. Semântica HTML | 3 | 1 | 1 | 0 |
| 6. Painéis hidden órfãos | 7 | 1 | 1 | 0 |
| 7. Elementos vazios | 13 | — | 1 | 0 |
| 8. Botões sem listeners | 5 | 1 | 1 | 0 |
| 9. Inputs sem labels | 0 | — | — | — |
| 10. Navegação/hierarquia | 3 | 1 | 1 | 0 |

**Total: 7 problemas críticos, 11 médios, 0 baixos**

---

## 1. Elementos fora de `</body>` (CRÍTICO)

| Linha | Problema | Impacto |
|---|---|---|
| 624–681 | `</body>` fecha na linha 624, mas dois `<aside>` inteiros (`#cards-panel` e `#friends-panel`) + `</html>` aparecem **após** o fechamento do body. O documento HTML é inválido. | **Crítico** |

**Descrição:** O `<script src="game.js" defer></script>` fecha o `<body>` na linha 624. Porém, as seções "Block Cards" (linhas 629–663) e "Amigos & Co-op" (linhas 668–679) foram inseridas **após** `</body>`, tornando o documento HTML inválido. Navegadores podem renderizar, mas o DOM fica imprevisível e validadores reprovam.

**Correção:** Mover os dois `<aside>` para dentro do `<main>` ou antes de `</body>`, e fechar `</body>` apenas na última linha antes de `</html>`.

---

## 2. IDs no HTML sem referência no JavaScript

IDs que existem no HTML mas **não** são referenciados pelo JS (nem via `getElementById`, `querySelector`, `aria-labelledby`, `aria-describedby`, `aria-controls`, nem `for`):

### Críticos

| Linha | ID | Impacto |
|---|---|---|
| 384 | `btn-skills-toggle` | **Crítico** — O JS referencia `btn-skills` (linha 4218), mas o HTML tem `btn-skills-toggle`. O botão não funciona. |
| 94 | `btn-powerups-toggle` | **Crítico** — Botão sem listener. O container `#powerups-bar-container` e `#powerups-active` também não são referenciados pelo JS. |

### Médios

| Linha | ID | Impacto |
|---|---|---|
| 465 | `btn-pvp-challenge` | **Médio** — Botão do painel PvP sem listener. Todo o painel PvP está órfão (ver item 6). |
| 504 | `btn-pvp-close` | **Médio** — Botão de fechar resultado PvP sem listener. |
| 286 | `skills-branches` | **Médio** — Container de skill tree sem referência JS. O painel skills funciona parcialmente (toggle, loading), mas o conteúdo nunca é populado. |

### IDs referenciados pelo JS mas **ausentes** no HTML

Estes IDs existem no JS mas não têm contraparte no HTML (elementos criados dinamicamente ou IDs desalinhados):

| ID no JS | Impacto |
|---|---|
| `btn-cards` | JS espera botão mobile nav para cards, mas HTML não o tem |
| `btn-season` | JS espera botão mobile nav para season, mas HTML não o tem |
| `btn-sprint-play-again` | JS espera botão de replay sprint, ausente no HTML |
| `market-sell-price` | JS espera input de preço para vender, ausente no HTML |
| `market-sell-select` | JS espera select de inventário para vender, ausente no HTML |
| `skills-content` | JS espera container de conteúdo de skills, ausente no HTML |
| `sprint-timer-display` | JS espera display de timer sprint, ausente no HTML |
| `sprint-timer-value` | JS espera valor de timer sprint, ausente no HTML |
| `sprint-leaderboard-list` | JS espera leaderboard sprint, ausente no HTML |
| `crate-icon` | JS espera ícone de crate, ausente no HTML |

---

## 3. Classes CSS ausentes

**43 classes** usadas no HTML não têm regra correspondente no CSS. A maioria concentra-se em 3 módulos:

### PvP (18 classes — módulo inteiro sem estilos)

| Linha | Classe |
|---|---|
| 456 | `.pvp-panel` |
| 458 | `.pvp-status` |
| 459 | `.pvp-status-text` |
| 461 | `.pvp-actions` |
| 462 | `.pvp-challenge-form` |
| 468 | `.pvp-match-info` |
| 469 | `.pvp-player-info` |
| 474 | `.pvp-player-found` |
| 472 | `.pvp-player-name` |
| 473 | `.pvp-player-score` |
| 476 | `.pvp-vs-badge` |
| 479 | `.pvp-player-label` |
| 484 | `.pvp-timer-bar-container` |
| 485 | `.pvp-timer-bar` |
| 486 | `.pvp-timer-text` |
| 488 | `.pvp-progress-container` |
| 489 | `.pvp-progress-label` |
| 490 | `.pvp-progress-bar-container` |
| 496 | `.pvp-result` |
| 497 | `.pvp-result-content` |
| 498 | `.pvp-result-icon` |
| 500 | `.pvp-result-text` |
| 499 | `.pvp-result-title` |
| 501 | `.pvp-result-scores` |

**Impacto:** **Crítico** — Todo o painel PvP (linhas 456–507) é funcionalmente inexistente: sem CSS, sem JS listeners, e sem integração com o resto do app.

### Crate (8 classes)

| Linha | Classe |
|---|---|
| 525 | `.crate-opening-animation` |
| 526 | `.crate-box` |
| 527 | `.crate-particles` |
| 531 | `.crate-result` |
| 532 | `.crate-item-reveal` |
| 533 | `.crate-item-icon` |
| 534 | `.crate-item-rarity` |
| 535 | `.crate-item-name` |
| 536 | `.crate-item-desc` |

**Impacto:** **Médio** — O modal de crate existe e tem listeners JS parciais, mas os elementos internos de revelação não têm estilos.

### Power-ups (4 classes)

| Linha | Classe |
|---|---|
| 91 | `.powerups-bar-container` |
| 92 | `.powerups-header` |
| 93 | `.powerups-label` |
| 94 | `.btn-powerups-toggle` |
| 96 | `.powerups-active` |

**Impacto:** **Médio** — Container inteiro sem estilos e sem JS.

### Market (3 classes)

| Linha | Classe |
|---|---|
| 245 | `.market-listings` |
| 252 | `.market-inventory` |
| 259 | `.market-sales-history` |

**Impacto:** **Baixo** — O mercado tem estrutura CSS parcial (`.market-section`, `.market-filters` existem), mas os containers de lista não têm regras próprias.

### Botões PvP (2 classes)

| Linha | Classe |
|---|---|
| 465 | `.btn-pvp-challenge` |
| 504 | `.btn-pvp-close` |

**Impacto:** **Médio** — Botões sem estilos visuais.

---

## 4. ARIA faltando em elementos interativos

| Linha | Elemento | Problema | Impacto |
|---|---|---|---|
| 324 | `<button role="radio" aria-checked="true">` | Botão de stake 1h tem `aria-checked="true"` mas o botão ativo (6h, linha 328) tem `aria-checked="false"`. Inconsistência. | **Médio** |
| 328 | `<button class="active" role="radio" aria-checked="false">` | Classe `.active` indica seleção, mas `aria-checked="false"` contradiz. | **Médio** |
| 332 | `<button role="radio" aria-checked="false">` | OK — não ativo, `false` correto. | — |

**Correção:** O botão com `.active` (6h) deve ter `aria-checked="true"` e o de 1h deve ter `aria-checked="false"`.

---

## 5. Semântica HTML incorreta

| Linha | Problema | Impacto |
|---|---|---|
| 1–682 | Ausência de `<h1>` | **Crítico** — O documento não tem `<h1>`. O título principal é `<title>` no `<head>`, mas o corpo começa direto com `<h2>`. A hierarquia de headings pula do nível 1 para o 2. |
| 375 | `aria-label="Navegacao do jogo"` | **Médio** — Falta acento: deveria ser `"Navegação do jogo"`. |
| 143 | `<svg id="lines-svg" ... hidden>` | **Médio** — O SVG que desenha as linhas de conexão entre células tem o atributo `hidden`. Ele nunca é desativado pelo JS (o JS usa `svgEl.replaceChildren()` e `svgEl.innerHTML = ''`), então as linhas nunca aparecem. |

**Correção do `<h1>`:** Adicionar `<h1>` no `<header>` ou no `<main>` com o título do jogo, ou promover o `<h2>` do tutorial para `<h1>`.

**Correção do SVG:** Remover o atributo `hidden` do `<svg id="lines-svg">`.

---

## 6. Painéis/sections hidden por padrão e nunca mostrados

Elementos com `hidden` que **não** são manipulados pelo JS:

| Linha | ID | Impacto |
|---|---|---|
| 91 | `#powerups-bar-container` | **Crítico** — Hidden, sem CSS, sem JS. Nunca aparece. |
| 456 | `#pvp-panel` | **Crítico** — Hidden, sem CSS, sem JS. Painel inteiro órfão. |
| 461 | `#pvp-actions` | **Médio** — Hidden, sem JS. |
| 468 | `#pvp-match-info` | **Médio** — Hidden, sem JS. |
| 496 | `#pvp-result` | **Médio** — Hidden, sem JS. |
| 510 | `#pvp-countdown-modal` | **Médio** — Hidden, sem JS. |

Elementos com `hidden` que **são** manipulados pelo JS (OK):
- `#btn-install-app`, `#pwa-update-banner`, `#level-bar-container`, `#global-event-banner`, `#boss-hud`, `#market-panel`, `#skills-panel`, `#staking-active`, `#chat-panel`, `#result-modal`, `#lightning-modal`, `#boss-defeat-modal`, `#achievements-modal`, `#achievement-toast`, `#crate-modal`, `#crate-result`, `#btn-close-crate`, `#decoder-modal`, `#decoder-feedback`, `#btn-close-decoder`, `#btn-decoder-launch`, `#season-panel`, `#season-content`, `#season-rewards-premium`, `#cards-panel`, `#cards-grid`, `#friends-panel`, `#friends-list`

---

## 7. Elementos com conteúdo vazio ou placeholder

### Estáticos vazios (sem JS populando)

| Linha | Elemento | Impacto |
|---|---|---|
| 96 | `<div id="powerups-active"></div>` | **Médio** — Vazio, sem JS. |
| 286 | `<div id="skills-branches"></div>` | **Médio** — Vazio, sem JS. |
| 485 | `<div id="pvp-timer-bar" style="width: 100%"></div>` | **Baixo** — Parte do painel PvP órfão. |
| 491 | `<div id="pvp-progress-challenger" style="width: 0%"></div>` | **Baixo** — Parte do painel PvP órfão. |
| 492 | `<div id="pvp-progress-challenged" style="width: 0%"></div>` | **Baixo** — Parte do painel PvP órfão. |
| 502 | `<span id="pvp-result-scores-detail"></span>` | **Baixo** — Parte do painel PvP órfão. |
| 515 | `<div id="pvp-countdown-words"></div>` | **Baixo** — Parte do painel PvP órfão. |
| 527 | `<div id="crate-particles"></div>` | **Baixo** — Vazio, sem JS. |
| 533 | `<span id="crate-item-icon"></span>` | **Baixo** — Vazio, sem JS. |
| 534 | `<span id="crate-item-rarity"></span>` | **Baixo** — Vazio, sem JS. |
| 535 | `<span id="crate-item-name"></span>` | **Baixo** — Vazio, sem JS. |
| 536 | `<span id="crate-item-desc"></span>` | **Baixo** — Vazio, sem JS. |

### Dinâmicos vazios (JS popula — OK)

`#level-bar-fill`, `#ui-energy-bar`, `#ui-energy-timer`, `#ui-network-progress`, `#global-event-icon`, `#global-event-label`, `#global-event-description`, `#global-event-countdown`, `#word-grid`, `#boss-hp-bar`, `#missions-list`, `#chat-messages`, `#chat-rate-info`, `#lightning-text`, `#achievements-summary`, `#achievements-filters`, `#achievements-grid`, `#achievement-toast-icon`, `#achievement-toast-title`, `#achievement-toast-desc`, `#decoder-timer-bar`, `#decoder-feedback`, `#season-progress-fill`, `#season-timer`, `#season-rewards-free`, `#season-rewards-premium`, `#cards-bonus`, `#cards-grid`, `#friends-coop-bonus`, `#friends-list`

---

## 8. Botões sem event listeners

| Linha | ID | Impacto |
|---|---|---|
| 384 | `#btn-skills-toggle` | **Crítico** — JS referencia `btn-skills` (sem `-toggle`). Botão não funciona. |
| 94 | `#btn-powerups-toggle` | **Crítico** — Sem listener, sem CSS, sem lógica. |
| 465 | `#btn-pvp-challenge` | **Médio** — Painel PvP inteiro órfão. |
| 504 | `#btn-pvp-close` | **Médio** — Painel PvP inteiro órfão. |

### Botões com delegation (OK)

- `#tab-browse`, `#tab-sell`, `#tab-history` — delegação via `querySelectorAll('.market-tab-btn')`
- Botões de staking duration — delegação via `querySelectorAll('.staking-duration-btn')`
- Botões de card filter — delegação via `querySelectorAll('.card-filter')`
- Botões de season tab — delegação via `querySelectorAll('.season-tab')`

---

## 9. Inputs sem labels ou aria-label

**OK:** Todos os inputs têm `aria-label` ou `<label for="...">` correspondente.

| Linha | Input | Mecanismo |
|---|---|---|
| 394 | `#miner-input` | `<label class="visually-hidden">` |
| 396 | `#pool-tag-input` | `<label>` visível |
| 398 | `#network-select` | `<label>` visível |
| 238 | `#market-filter-powerup` | `aria-label` |
| 320 | `#staking-amount-input` | `<label for="...">` |
| 367 | `#chat-input` | `aria-label` |
| 464 | `#pvp-target-input` | `<label>` visível |
| 567 | `#decoder-input` | `aria-label` |
| 672 | `#friends-add-input` | `aria-label` |

---

## 10. Estrutura de navegação e hierarquia visual

### Problemas

| Linha | Problema | Impacto |
|---|---|---|
| 1–682 | Sem `<h1>` no documento | **Crítico** — A hierarquia de headings começa em `<h2>`. Adicionar `<h1>` no `<header>` ou no modal de tutorial. |
| 375 | `aria-label="Navegacao do jogo"` | **Médio** — Falta acento em "Navegação". |
| 375–385 | `<nav>` contém apenas links e botões mobile | **Médio** — O nav não inclui botões para todos os painéis existentes (cards, friends, season, staking, missions). |

### Observações

- **Skip link** (linha 21): Presente e funcional, aponta para `#word-grid`.
- **`<main>`** (linha 104): Presente, contém a área de jogo e painéis laterais.
- **`<header>`** (linha 35): Presente, contém dashboard e stats.
- **`<footer>`**: Ausente. Não é crítico para um jogo, mas seria útil para créditos/versão.
- **`<nav>`** (linha 375): Navegação mobile com 6 itens. Painéis como cards, friends, season e staking não têm entrada de navegação.

---

## Priorização de correções

### Fase 1 — Crítico (corrigir imediatamente)

1. **Mover `#cards-panel` e `#friends-panel` para dentro de `</body>`** (linhas 629–679)
2. **Renomear `btn-skills-toggle` para `btn-skills`** (linha 384) ou atualizar o JS (linha 4218)
3. **Remover `hidden` do `<svg id="lines-svg">`** (linha 143)
4. **Adicionar `<h1>`** no documento
5. **Remover ou implementar o painel PvP** (linhas 456–507) — está completamente órfão

### Fase 2 — Médio (próximo sprint)

1. **Corrigir `aria-checked` nos botões de staking** (linhas 324, 328)
2. **Adicionar CSS para classes de crate** (9 classes faltantes)
3. **Implementar ou remover `#powerups-bar-container`** (linhas 91–97)
4. **Corrigir `aria-label` do nav** (linha 375)
5. **Adicionar IDs ausentes no HTML** que o JS espera: `btn-cards`, `btn-season`, `btn-sprint-play-again`, `market-sell-price`, `market-sell-select`, `skills-content`, `sprint-timer-display`, `sprint-timer-value`, `sprint-leaderboard-list`, `crate-icon`

### Fase 3 — Baixo (melhoria contínua)

1. **Adicionar `<footer>`** com versão/créditos
2. **Expandir `<nav>`** para incluir todos os painéis
3. **Adicionar CSS para classes de market** (3 classes faltantes)
4. **Limpar elementos vazios órfãos** do PvP e crate

---

## Métricas

- **IDs no HTML:** 224
- **IDs referenciados no JS:** 147
- **IDs órfãos (HTML sem JS):** 53
- **IDs esperados pelo JS mas ausentes no HTML:** 10
- **Classes no HTML:** ~180
- **Classes sem CSS:** 43
- **IDs duplicados:** 0
- **Inputs sem label:** 0
- **Botões sem listener:** 5 (2 críticos)
- **Elementos fora de `</body>`:** 2 painéis inteiros
