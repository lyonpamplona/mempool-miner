# Fechamento — Correção das Mecânicas (2026-08-21)

Este documento registra a aplicação do plano de correção derivado da
`AUDITORIA-MECANICAS-2026-08-21.md`. Cada fase foi aplicada no working tree
(sem commit — commit é manual, por decisão do usuário), rebuildada e validada
funcionalmente antes de avançar.

## Estado geral

| Fase | Escopo | Status | Validação |
|------|--------|--------|-----------|
| 1 | Crates, Skill Tree, Power-ups | ✅ Aplicada | Contratos 422→400; fluxo claim→abrir→item; power-ups creditados |
| 2 | XP, Season, Conquistas, Cards, Energia | ✅ Aplicada | add-xp 200; card credit `new:true`; energia `next_refill_at` |
| 3 | Boss, Eventos Globais, Staking, Sessão | ✅ Aplicada | reset no timeout; contrato de datas; seletor 1/6/24h; clearSessionState |
| 4 | CSS da migração (91 itens) | ✅ Aplicada | 91 classes/keyframes/vars; chaves balanceadas; servido via curl |
| 5 | Higiene e docs | ⚠️ Parcial | docs/MECANICAS.md excluído no working tree (não recriado sem confirmação) |

**Testes:** `pytest backend/tests` → **124 passed, 3 failed**. As 3 falhas são
**pré-existentes** (relay PubSub em `main.py:1873-1885`, código não tocado nesta
sessão; o commit mais recente é "fix: relay PubSub"). Nenhum teste novo falhou
por causa das correções.

**Deploy:** `CACHE_VERSION` v18 → **v20** (shell mudou: game.js, index.html,
pixel.css). 7/7 containers healthy.

---

## Fase 1 — Desbloquear o que estava quebrado

### 1.1 Crates
- `openCrate` (game.js): payload `is_free` → **`use_free`** (bate com
  `CrateOpenRequest`, `extra=forbid`). Antes: HTTP 422 em toda abertura.
- `showCrateResult`: lê `result.item` (objeto `name/rarity/value/icon`), não
  campos soltos `rarity`/`value` (que eram `undefined`).
- `index.html`: botão "50K" → **"5K"** (preço real `CRATE_PRICES` = 5.000 sats).

### 1.2 Skill Tree
- `unlockSkill`: payload `{branch, level}` → **`{username, branch}`** (bate com
  `SkillUpgradeRequest`, `extra=forbid`). Antes: 422 em todo upgrade.
- `renderSkillTree`: lê `player_level` (não `level`), `node.description` (não
  `node.effect`); o nó clicável é o **próximo nível**
  (`node.level === current_level + 1`), não depende de `node.available`
  (campo que o backend não envia). Antes: nenhum nó era clicável.

### 1.3 Crates grátis
- Nova `claimFreeCrates()` chamada em `showResult` após `trackBlockCompleted`
  (1 crate a cada 10 blocos). Antes: `crates/claim` era rota órfã.

### 1.4 Power-ups
- `loadPowerupsInventory`: agora carrega o **inventário pessoal**
  (`GET /powerups/{username}`), não o mercado (stub `return loadMarketInventory()`).
- `renderPowerupsPanel` + `activatePowerup` (ativa via API).
- 5 efeitos aplicados na partida:
  - `time_freeze`: pausa o timer em `startNetworkRace`
  - `scanner`: revela a direção de uma palavra
  - `double_combo`: teto de combo 4× → 6×
  - `magnet`: +50% de sats na rodada
  - `precision`: isenta do slashing
- Estado `powerupEffects` aplicado no início da rodada
  (`applyPendingPowerups`) e resetado no fim (`resetRoundPowerups`).

### Bug de backend descoberto e corrigido (crates)
- `CRATE_POWERUPS` usava IDs inválidos (`speed_boost/golden_eye/...`) que não
  existem em `POWERUP_DEFINITIONS` → corrigido para
  `time_freeze/scanner/double_combo/magnet/precision`.
- `crates/open` **não creditava** o power-up no inventário quando o drop era
  power-up → agora faz `sadd` em `powerups_key`.

---

## Fase 2 — Reconectar as progressões

- **XP de nível + Season Pass:** `addXP` + `addSeasonXP` chamados a cada palavra
  (100% do XP). Antes: `addXP`/`calculateWordXP` e a rota `season add-xp` eram
  código morto → jogador travado no nível 1 / temporada inativa.
- **Bônus de conquistas:** `applyAchievementBonus` na pontuação +
  `getHintPrice()` em `buyHint`. Antes: nunca chamados.
- **Cards:** `renderCardsUI` lê `total` (não `totals`) e trata
  `collection_bonus` como objeto.
- **Energia:** `updateEnergyUI` lê `next_refill_at` (timestamp UNIX s, não
  `nextRefill`); botão "10K SATS" → **"2,000 SATS"**.
- **Bug de backend descoberto e corrigido (cards):** o conjunto de cards do
  jogador **nunca era populado** (o ingestor só grava o conjunto global).
  Criado `POST /cards/{username}/credit` + `creditBlockCard()` no handler
  `block_mined` + animação de card pull quando `result.new`.

---

## Fase 3 — Lógica de gameplay

- **Boss:** `resetBossState()` no caminho de derrota por timeout
  (`showBossResult(false)`). Antes: só o modal de vitória resetava →
  `isBossActive` ficava `true` e gerava "rodadas de boss fantasma" em cadeia.
- **Eventos globais:** handler WS lê `event_ends_at`/`event_started_at`
  (não `ends_at`/`started_at`); efeitos de grade/tempo/recompensa aplicados em
  `buildPlayableBlock` (lightning_storm 8×8/20s/10×, mempool_flood 15×15/2×,
  fee_spike 3×, golden_rush 5×); `loadActiveGlobalEvent` normaliza o shape do REST.
- **Staking:** `<select id="staking-duration">` 1/10/100 Blocks → **1/6/24
  Hours** (aceitos pelo `STAKE_BONUS_TABLE`) + listener `change` sincroniza
  `selectedStakeDuration`.
- **Sessão:** `clearSessionState()` no `teardownSession` quando
  `reason !== 'page-hide'` (page-hide preserva para restauração).

---

## Fase 4 — CSS da migração

Adicionado ao final do `pixel.css` (coerente com o design system mecha sci-fi:
cantos retos, fontes mono, paleta do `:root`):

- **3 variáveis** em `:root`: `--error-red`, `--lightning-blue`,
  `--warning-orange`.
- **~80 classes de item dinâmico** (geradas pelo JS, antes sem estilo):
  `floating-text`, `rank-item`/`top-1/2/3`, `boss-loot-text`,
  `block-card-*` (+raridades), `chat-message-*`, `friend-*`, `market-listing-*`
  /`market-history-*`, `season-reward-*`, `skill-*`, `achievement-*`,
  `crate-modal-*`/`rarity-*`, `staking-history-*`.
- **11 keyframes** (referenciados mas nunca definidos): `bossFlash`,
  `bossShake`, `bossHpDamage`, `bossIconPulse`, `bossDefeatPulse`,
  `halvingFlash`, `slashingFlash`, `rbfPulse`, `levelUpPulse`, `chatMsgIn`,
  `crateReveal`.

Validação: 91/91 itens presentes; chaves balanceadas (751/751); servido via
curl (63 referências às classes novas + 3 variáveis).

---

## Fase 5 — Higiene e docs

- **docs/MECANICAS.md** (e todo `docs/`, exceto o relatório de auditoria) está
  **excluído no working tree** (`git status` mostra ` D`). Não recriado sem
  confirmação do usuário. As divergências docs↔código identificadas pela
  auditoria (MEV +50.000 sats, 30 conquistas, 11 ranks, 4 níveis de hardware,
  loja em UPGRADES, pools/leaderboard em COMPETIR) devem ser refletidas quando
  o documento for restaurado.
- **Código morto** (handlers de elementos que não existem no HTML, ex.
  `.staking-duration-btn`, `.market-tab`, `.season-tab`): deixado intacto por
  respeito à estrutura existente — são no-ops inofensivos.

---

## Pontas soltas conhecidas (para acompanhamento)

- **3 testes pré-existentes** em `test_models.py` (relay PubSub/websocket) —
  fora do escopo desta correção; o commit "fix: relay PubSub" não resolveu.
- **docs/** excluído no working tree — restaurar e atualizar MECANICAS.md.
- **Bônus co-op de amigos** (`co_op_bonus`) é apenas exibido; aplicação em
  gameplay não verificada.
- **`trackPoolRank1`** nunca é chamada (código morto, baixo impacto).

## Próximo passo
Auditoria final com 3 agents (lógica F1-2, lógica F3, CSS F4 + varredura) para
confirmar que cada correção está correta e caçar pontas soltas restantes.
