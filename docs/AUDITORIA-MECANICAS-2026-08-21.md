# Auditoria Completa de Mecânicas — Mempool Miner

**Data:** 2026-08-21 · **Método:** 3 agents de auditoria em paralelo (JOGO / UPGRADES+COMPETIR / PERFIL+SOCIAL+transversais) + análise estática de cruzamento (JS↔HTML↔CSS↔API) + validação de runtime (containers, API, WebSocket) + validação manual de pontos conflitantes.
**Arquivos auditados:** `frontend/game.js` (6.479 linhas), `frontend/pixel.css` (2.560), `frontend/index.html` (607), `backend/app/main.py` (5.028), `ingestor.py`, `engine.py`, `global_events.py`, `season_pass.py`, `service-worker.js`, contra `docs/MECANICAS.md`.
**Modo:** somente leitura — nenhum arquivo foi modificado.

---

## 1. Veredito executivo

**O jogo roda de ponta a ponta** (coleta BIP39, grade, seleção, pontuação, raridades, RBF, loja, decoder, chat, amigos, mercado, missões, sprint, ranking, energia, staking, PWA, sessão — todos funcionais no núcleo), **mas a migração de design deixou 5 mecânicas quebradas/inativas e ~97 classes CSS de item dinâmico sem estilo**:

| Categoria | Qtd | Resumo |
|---|---|---|
| 🔴 **Crítica** (mecânica quebrada/inativa) | **5** | Crates (422), Skill Tree (422 + nós não clicáveis), XP de nível (nunca concedido), Season Pass (progressão morta), Power-ups (efeitos nunca aplicados) |
| 🟠 **Alta** (ponta solta lógica material) | **5** | Boss (derrota por timeout gera rodadas fantasma), Eventos globais (efeitos de grade/tempo ausentes), Staking (seletor de duração desconectado), Conquistas (bônus nunca aplicados), Cards (campos divergentes → "undefined") |
| 🟡 **Média** | **6** | Contrato de datas dos eventos, timer de energia, ~97 classes CSS ausentes, floating-text, rank-item/top-N, clearSessionState nunca chamado |
| 🟢 **Baixa** | **9** | 8 keyframes indefinidos, 3 CSS vars indefinidas, boss-loot-text, desconto de hint não aplicado, divergências docs↔código, código morto |

**Causa raiz transversal:** a migração de design portou o *shell* (as 73 classes obfuscadas `u-inline-*` do HTML estão 100% mapeadas no CSS) mas **não portou as classes de *item* geradas dinamicamente pelo JS** nem conectou vários pipelines de progressão (XP, season, crates grátis, bônus de conquistas, efeitos de power-up) ao loop de jogo. O backend está íntegro — todas as rotas existem e os contratos internos batem; as quebras estão no frontend (payloads divergentes, funções órfãs, campos lidos com nome errado).

---

## 2. Baseline de runtime (validado em 2026-08-21)

- **7/7 containers healthy** (backend, frontend, redis, ingestores regtest+signet, nós regtest+signet)
- API `ready`; regtest e signet jogáveis; mainnet desabilitada (opt-in)
- WebSocket `/ws/v1/game/regtest` → `101 Switching Protocols` (funciona; exige header `Origin` — nginx)
- Todas as rotas de API respondem (200 com parâmetros corretos)
- Service Worker `CACHE_VERSION = 'v18'` ativo; cacheia apenas o shell; `/api` e `/ws` nunca entram no cache

---

## 3. Inventário de mecânicas (30 auditadas)

### Aba JOGO (11)

| # | Mecânica | Status |
|---|---|---|
| 1 | Coleta BIP39 (6 únicas, dedupe, limpeza por bloco) | ✅ FUNCIONAL |
| 2 | Grade caça-palavras (12×12 / 8×8 L2 / 15×15 vsize>1000) | ✅ núcleo + 🟠 eventos globais não aplicam grade |
| 3 | Seleção (Pointer Events + teclado, 8 direções) | ✅ FUNCIONAL |
| 4 | Pontuação (fórmula + combo) | ✅ FUNCIONAL (docs divergem: base tem decaimento de halving) |
| 5 | Raridades (Golden ×5, HighFee ×3, ×15, MEV) | ✅ FUNCIONAL (docs divergem: MEV paga +50.000 sats) |
| 6 | RBF / bloco órfão | ✅ FUNCIONAL |
| 7 | Boss block | 🟠 PONTA SOLTA LÓGICA (derrota por timeout quebra estado) |
| 8 | Eventos globais | 🟠 PONTA SOLTA LÓGICA (efeitos de grade/tempo ausentes + contrato de datas) |
| 9 | Loja (hint/hardware/Lightning) | ✅ FUNCIONAL (desconto de hint não aplicado — baixa) |
| 10 | Pools | ✅ lógica + 🟡 sem CSS (`rank-item`) |
| 11 | Leaderboard | ✅ lógica + 🟡 sem CSS (`rank-item`) |

### Aba UPGRADES (3)

| # | Mecânica | Status |
|---|---|---|
| 12 | LOJA (hint/hardware/Lightning/energia) | ✅ FUNCIONAL |
| 13 | INVENTÁRIO — Power-ups | 🔴 PONTA SOLTA LÓGICA (efeitos nunca aplicados; inventário mostra o mercado) |
| 14 | UTILITÁRIOS — Decoder | ✅ FUNCIONAL (100%) |

### Aba COMPETIR (3)

| # | Mecânica | Status |
|---|---|---|
| 15 | RANKING | ✅ lógica + 🟡 sem CSS |
| 16 | MISSÕES | ✅ lógica + 🟡 12 classes sem CSS |
| 17 | SPRINT | ✅ lógica + 🟡 13 classes sem CSS |

### Aba PERFIL (4)

| # | Mecânica | Status |
|---|---|---|
| 18 | VISÃO | 🟡 resumo do jogador não existe na seção (só cards estáticos) |
| 19 | PROGRESSÃO (nível/XP/rank) | 🔴 XP nunca concedido (nível 1 para sempre) |
| 20 | COLEÇÃO (cards) | 🟡 campos divergentes + 6 classes sem CSS + animação morta |
| 21 | ECONOMIA (staking) | 🟠 seletor de duração desconectado (sempre 6h) |

### Aba SOCIAL (3)

| # | Mecânica | Status |
|---|---|---|
| 22 | CHAT | ✅ lógica + 🟡 7 classes sem CSS |
| 23 | EQUIPE (amigos) | ✅ lógica + 🟡 6 classes sem CSS |
| 24 | MERCADO | ✅ lógica + 🟡 11 classes sem CSS |

### Transversais (6)

| # | Mecânica | Status |
|---|---|---|
| 25 | Conquistas | 🟠 bônus nunca aplicados + 8 classes sem CSS |
| 26 | Season Pass | 🔴 progressão morta (add-xp nunca chamado) |
| 27 | Energia | ✅ funciona; 🟡 timer de recarga nunca exibido (campo divergente) |
| 28 | Crates | 🔴 QUEBRADA (422 em toda abertura + claim nunca chamado) |
| 29 | Skill Tree | 🔴 QUEBRADA (422 + nós nunca clicáveis) |
| 30 | PWA / Sessão | ✅ FUNCIONAL (clearSessionState nunca chamado — baixa) |

---

## 4. Pontas soltas CRÍTICAS (mecânicas quebradas/inativas)

### C1 — Crates: HTTP 422 em toda abertura 🔴
- **Evidência:** `game.js:6241` envia `{ username, is_free }`; o backend exige `use_free` com `extra="forbid"` (`CrateOpenRequest`, `main.py:3602-3608`).
- **Impacto:** loot boxes totalmente inativas — os botões "FREE" e "50K" (o preço real é 5.000 sats, `CRATE_PRICES` `main.py:3502`) nunca funcionam.
- **Ponta extra:** `showCrateResult` lê `const { item, rarity, value } = result` (`game.js:6263`), mas o backend retorna `{ item: <objeto>, crates_remaining, legendary_bonus }` (`main.py:3688-3695`) → `rarity`/`value` undefined.
- **Ponta extra:** `POST /crates/claim` (`main.py:3744`) **nunca é chamada** pelo JS → a mecânica "1 crate grátis a cada 10 blocos" está morta (o JS rastreia `blocksCompletedTotal` via `pushStats`, mas nunca converte em crates).

### C2 — Skill Tree: HTTP 422 + nós nunca clicáveis 🔴
- **Evidência:** `game.js:4671` envia `{ branch, level }`; o backend exige `{ username, branch }` com `extra="forbid"` (`SkillUpgradeRequest`, `main.py:1618-1624`) → 422 em todo upgrade.
- **Segunda quebra (independente):** `renderSkillTree` só anexa o handler de clique quando `node.available` é true (`game.js:4649-4651`), mas o backend **não retorna `available`** nos nós (só `level/name/description/unlocked`, `main.py:1701-1706`) → nenhum nó é clicável mesmo sem o 422.
- **Terceira divergência:** JS lê `node.effect` (`game.js:4644`) — backend fornece `description` → exibe "undefined"; JS lê `level` do topo (`game.js:4595`) — backend fornece `player_level` (`main.py:1720`) → header exibe undefined.
- **Impacto:** habilidades permanentes (tempo, busca, lightning) inacessíveis.

### C3 — XP de nível nunca concedido 🔴
- **Evidência:** `addXP` (`game.js:6429`) e `calculateWordXP` (`game.js:6470`) estão definidos mas **nunca são chamados** (zero call sites fora da definição). O handler `block_mined` (`game.js:1377`) e o loop de palavras (`endSelection`) não disparam XP.
- **Impacto:** o jogador fica no nível 1 para sempre; rank e bônus passivos (`time_bonus`, `hint_discount`) congelados. A rota `POST /level/{username}/add-xp` (`main.py:4979`) existe e é íntegra, mas é órfã.
- **Nota:** os bônus de nível são aplicados via `window.NETWORK_TIME_BONUS`/`window.HINT_DISCOUNT` (`game.js:6415-6425`) — variáveis globais que nenhum outro trecho do JS lê (efeito duvidoso).

### C4 — Season Pass: progressão morta 🔴
- **Evidência:** a rota `POST /season/{username}/add-xp` (`main.py:4751`) **nunca é chamada** pelo JS (a única `add-xp` no JS é a de nível, `game.js:6431`).
- **Impacto:** o nível da temporada fica em 0 para sempre; nenhuma recompensa desbloqueia; `claimSeasonReward` sempre falha com "level_locked" (`season_pass.py:249-251`). Só a compra de premium funciona.
- **Nota:** backend íntegro (20 free + 20 premium, 100 XP/nível, premium 50.000 sats). Divergência docs: docs dizem "28 dias"; o código usa temporadas trimestrais (`SEASON_DURATION_DAYS = 28` definido mas nunca usado, `season_pass.py:10`).

### C5 — Power-ups: efeitos nunca aplicados na partida 🔴
- **Evidência:** o backend armazena timers em `active_timers` (`powerups/activate`, `main.py:2237-2246`), mas **nenhum código em game.js lê `active_timers` ou aplica efeitos** durante a partida.
- **Segunda ponta:** `loadPowerupsInventory()` (`game.js:360-362`) é apenas um alias de `loadMarketInventory()` → a aba INVENTÁRIO mostra o mercado P2P, não o inventário pessoal do jogador.
- **Divergência docs (importante):** `docs/MECANICAS.md` lista power-ups `speed_boost/golden_eye/combo_lock/extra_time/double_sats`; o código real (`POWERUP_DEFINITIONS`, `main.py:2097-2143`) usa **`time_freeze/scanner/double_combo/magnet/precision`** — os docs estão desatualizados (código é a fonte de verdade).
- **Impacto:** o jogador gasta sats para ativar power-ups que nunca produzem efeito.

---

## 5. Pontas soltas ALTAS

### A1 — Boss block: derrota por timeout quebra o estado 🟠
- **Evidência:** timeout do boss chama `showBossResult(false)` (`game.js:3164`); o botão "Tentar novamente" executa só `prepareNextBlock` (`game.js:3197`) **sem `resetBossState`** (que só é chamado pelo modal de vitória, `game.js:3254`).
- **Impacto:** após o boss "resistir", `isBossActive` fica `true`, o HUD do boss permanece sobre a grade em rodadas normais e as próximas 10 transações re-disparam `buildBossPlayableBlock` (`game.js:1357-1361`, `3016-3022`) → **rodadas de boss fantasma em cadeia** (15×15, 45 s, ×5) sem evento do backend.

### A2 — Eventos globais: efeitos de grade/tempo não aplicados 🟠
- **Evidência:** `buildPlayableBlock` (`game.js:1878-1887`) só considera `isLightningMode` (comprado) e `vsize>1000`. Durante `mempool_flood` a grade não vira 15×15 obrigatória nem ganha +15 s; durante `lightning_storm` não vira 8×8. O backend tem `get_event_grid_size` (`engine.py:405-415`) e o campo `expand_grid` (`engine.py:207`), mas o frontend ignora ambos.
- **Impacto:** o efeito principal documentado de 2 dos 4 eventos globais não acontece; só o multiplicador de recompensa (via `multiplier` do backend) funciona.

### A3 — Staking: seletor de duração desconectado 🟠
- **Evidência:** o HTML tem `<select id="staking-duration">` com opções `1/10/100 "Blocks"` (`index.html:362-366`), mas o backend só aceita **1, 6 ou 24 horas** (`STAKE_BONUS_TABLE`, `main.py:3827-3831`). O JS usa `selectedStakeDuration` (hardcode 6, `game.js:3938`) e **ignora o valor do select**; os botões `.staking-duration-btn` que deveriam atualizá-lo (`game.js:4282-4292`) **não existem no HTML**.
- **Impacto:** o jogador vê "1/10/100 Blocks", não consegue escolher, e o stake sempre sai em 6h.

### A4 — Conquistas: bônus nunca aplicados ao gameplay 🟠
- **Evidência:** `applyAchievementBonus` (`game.js:2859`) e `getHintPrice` (`game.js:2853`) **nunca são chamados** → os bônus de recompensa/desconto de dica são calculados e exibidos no modal, mas não afetam pontuação nem preço de hint (`docs/MECANICAS.md:303` afirma que são aplicados).
- **Nota:** o rastreamento está ativo (`trackWordFound`/`trackCombo` no loop de palavras, `game.js:2341-2342`; `trackBlockCompleted` etc.) e o backend é íntegro. Divergência docs: docs dizem 28 conquistas; o código tem **30** (`main.py:927-963`).

### A5 — Cards: campos divergentes → "undefined" 🟠
- **Evidência:** JS lê `totals` (`game.js:5154`) mas o backend retorna `total` (`main.py:3475`) → campo TOTAL exibe "undefined". JS trata `collection_bonus` como número (`game.js:5164-5166`) mas o backend retorna **objeto** por raridade (`main.py:3461-3477`) → exibe "[object Object]".
- **Pontas extras:** filtro de raridade morto (`document.querySelectorAll('.card-filter')` `game.js:5238` — não existe nenhum `.card-filter` no HTML); `showCardPullAnimation` nunca é chamada (zero call sites) → animação de card pull é código morto.

---

## 6. Pontas soltas MÉDIAS

| # | Ponta | Evidência | Impacto |
|---|---|---|---|
| M1 | Contrato de datas dos eventos globais divergente | `game.js:5707` lê `ends_at`/`started_at`; backend envia `event_ends_at`/`event_started_at` (`main.py:153-154`, `global_events.py:328-329`) | `event.endsAt` chega `undefined`; countdown usa fallback local (`game.js:5662`); pré-anúncio (120 s) e fim do evento podem divergir do estado real |
| M2 | Timer de recarga de energia nunca exibido | JS lê `nextRefill` (`game.js:4753`); backend retorna `next_refill_at` (`main.py:4322`) | o timer de regeneração nunca aparece |
| M3 | ~97 classes de item dinâmico sem CSS (migração incompleta) | ver §7 | itens renderizam sem estilo (ver por domínio abaixo) |
| M4 | `.floating-text` sem CSS | `game.js:2409` (ausente no pixel.css) | o feedback flutuante de pontos ("+1.250 Sats (GOLDEN)") é anexado ao `<body>` sem `position`/animação (o keyframe `floatUp` existe mas nada o referencia) — o jogador não vê a recompensa |
| M5 | `.rank-item` / `.top-N` sem CSS | `game.js:1565, 1619` | leaderboard e pools renderizam como texto puro sem layout/destaque top-3 |
| M6 | `clearSessionState` nunca chamado | `game.js:284` (zero call sites) | ao encerrar a sessão, o estado antigo persiste em `sessionStorage` e é restaurado no próximo F5 (saldo/realm de sessão anterior) |

## 7. Classes CSS de item ausentes no `pixel.css` (migração incompleta)

O shell (73 classes `u-inline-*` do HTML) está 100% mapeado. O que falta são as classes de **item gerado dinamicamente pelo JS**:

| Domínio | Classes ausentes | Qtd |
|---|---|---|
| Missões | `mission-card`, `mission-header`, `mission-title`, `mission-reward`, `mission-description`, `mission-progress-container`, `mission-progress-fill`, `mission-progress-text`, `mission-type-badge`, `missions-weekly-section`, `missions-weekly-label`, `btn-claim` | 12 |
| Sprint | `sprint-leaderboard-item`, `sprint-leaderboard-rank`, `sprint-leaderboard-name`, `sprint-leaderboard-time`, `sprint-result-overlay`, `sprint-result-card`, `sprint-result-title`, `sprint-result-stats`, `sprint-result-stat`, `sprint-result-stat-label`, `sprint-result-stat-value`, `sprint-result-btn`, `sprint-timer-display` | 13 |
| Mercado | `market-listing-icon`, `market-listing-info`, `market-listing-name`, `market-listing-seller`, `market-listing-price`, `market-listing-price-value`, `market-listing-price-label`, `market-listing-buy-btn`, `market-history-item`, `market-history-powerup`, `market-empty` | 11 |
| Skill Tree | `skill-branch`, `skill-branch-title`, `skill-branch-desc`, `skill-nodes`, `skill-node`, `skill-node-icon`, `skill-node-info`, `skill-node-level`, `skill-node-effect` | 9 |
| Conquistas | `achievement-icon`, `achievement-name`, `achievement-progress-bar`, `achievement-progress-fill`, `achievement-progress-text`, `achievement-tooltip`, `achievement-tooltip-desc`, `achievement-tooltip-bonus`, `summary-count`, `summary-bonus` | 10 |
| Season | `season-reward-item`, `season-reward-icon`, `season-reward-name`, `season-reward-type`, `season-reward-level`, `season-reward-info`, `season-reward-claim` | 7 |
| Cards | `block-card`, `block-card-icon`, `block-card-hash`, `block-card-rarity`, `block-card-stats`, `block-card-tooltip` | 6 |
| Chat | `chat-message`, `chat-message-header`, `chat-message-username`, `chat-message-time`, `chat-message-text`, `chat-rate-info`, `chat-emoji-btn` | 7 |
| Amigos | `friend-info`, `friend-name`, `friend-status`, `friend-meta`, `friend-remove-btn`, `friends-empty` | 6 |
| Staking | `staking-history-item`, `staking-history-type`, `staking-history-amount`, `staking-history-date`, `stake-created`, `stake-unstake`, `stake-expired` | 7 |
| Crates | `crate-modal-overlay`, `crate-modal-content`, `crate-result-title`, `crate-result-item`, `crate-result-rarity`, `crate-close-btn`, `rarity-common`, `rarity-uncommon`, `rarity-rare`, `rarity-epic`, `rarity-legendary` | 11 |
| Ranking | `rank-item`, `top-1`, `top-2`, `top-3` | 4 |
| Diversos | `floating-text`, `boss-loot-text` | 2 |

**Total: ~97 classes.** (Os contêineres/painéis — `missions-list`, `skills-branches`, `season-rewards-list`, `chat-messages`, `friends-list`, `cards-grid`, `market-listings`, `sprint-leaderboard-list` — existem no CSS; falta o *item*.)

## 8. Pontas soltas BAIXAS

| # | Ponta | Evidência | Impacto |
|---|---|---|---|
| B1 | **RESOLVIDO** — keyframes | animações de boss, halving, slashing e RBF estão definidas em `pixel.css` | efeitos ativos |
| B2 | **RESOLVIDO** — variáveis CSS | `--error-red`, `--lightning-blue` e `--warning-orange` estão definidas no `:root` | cores consistentes |
| B3 | **RESOLVIDO** — `.boss-loot-text` | regra presente em `pixel.css` | loot estilizado |
| B4 | **RESOLVIDO** — desconto de dica | `buyHint()` usa `getHintPrice()`, composto a partir dos bônus atuais | desconto aplicado |
| B5 | **RESOLVIDO** — timer Sprint único | usa `#sprint-timer-display` do HTML; criação JS é somente fallback quando o elemento não existe | sem duplicação |
| B6 | **RESOLVIDO** — rótulo de energia | HTML mostra `2,000 SATS`, igual ao custo real; o JS preserva o markup original | consistente |
| B7 | **RESOLVIDO** — rótulo de crate | HTML mostra `5K`, igual ao preço real de 5.000 sats | consistente |
| B8 | **RESOLVIDO** — código morto/integrações | `toggleChatPanel` e `trackPoolRank1` removidas; `showCardPullAnimation` é chamada no claim de card; `crates/claim` é chamado nos fluxos de bloco concluído | sem dívida remanescente nesses símbolos |
| B9 | Divergências docs↔código | ver §9 | docs desatualizados |

## 9. Divergências docs↔código (código é a fonte de verdade)

| Item | docs/MECANICAS.md | Código real |
|---|---|---|
| Power-ups | `speed_boost/golden_eye/combo_lock/extra_time/double_sats` | `time_freeze/scanner/double_combo/magnet/precision` (`main.py:2097-2143`) |
| Conquistas | 28 | 30 (`main.py:927-963`) |
| Ranks | 10 tiers | 11 (inclui "Satoshi" nível 100, `main.py:4908`) |
| MEV | "×1, sem bônus direto" | paga +50.000 sats (`game.js:2326-2333`) |
| Hardware | "CPU → GPU → ASIC" (3 níveis) | 4 níveis (inclui "Quantum Node", `game.js:293`) |
| Pontuação base | 500 fixa | aplica decaimento de halving (`game.js:1891-1893`) |
| Season | "28 dias" | temporadas trimestrais (`SEASON_DURATION_DAYS=28` definido mas nunca usado) |
| Loja | aba JOGO | está em UPGRADES/LOJA (`index.html:227-260`) |
| Pools/Leaderboard | sob JOGO | UI em COMPETIR/RANKING (`index.html:299-306`) |
| Sessão | "9 pontos críticos" | 11 campos salvos (`game.js:258-274`) |

---

## 10. Plano de correção (priorizado em fases)

Critério de ordem: **primeiro o que está quebrado (422 / mecânica inativa), depois o que está desconectado (progressões mortas), depois o visual (CSS da migração), por último cosmético/docs.** Cada fase termina com `docker compose up --build -d`, health check dos 7 containers e validação funcional antes de avançar (estilo de trabalho padrão).

### FASE 1 — Desbloquear o que está quebrado (422 / inativo) 🔴
| # | Correção | Arquivo | Esforço |
|---|---|---|---|
| 1.1 | **Crates:** trocar payload `is_free` → `use_free` em `openCrate` (`game.js:6241`); corrigir `showCrateResult` para ler `item` (objeto) + `crates_remaining`/`legendary_bonus` (`game.js:6263`); corrigir rótulo "50K" → "5K" (`index.html:272`) | game.js, index.html | ~1h |
| 1.2 | **Skill Tree:** trocar payload `{branch, level}` → `{username: minerName, branch}` em `unlockSkill` (`game.js:4671`); remover dependência de `node.available` (usar `!node.unlocked` + pontos disponíveis); ler `description` em vez de `effect` e `player_level` em vez de `level` (`game.js:4595,4644`) | game.js | ~1h |
| 1.3 | **Crates grátis:** chamar `POST /crates/claim` com `{username, blocks_mined: blocksCompletedTotal}` no handler `block_mined` (após `trackBlockCompleted`), e atualizar `crateFreeCountEl` com o retorno | game.js | ~1h |
| 1.4 | **Power-ups:** (a) `loadPowerupsInventory` deve chamar `powerups/{username}` (inventário pessoal + `active_timers`), não o mercado; (b) aplicar efeitos de `active_timers` na partida: `time_freeze` (pausa timer 5 s), `scanner` (revela direção de 1 palavra), `double_combo` (combo máx 6×), `magnet` (+50% sats na rodada), `precision` (sem slashing na rodada) | game.js | ~3-4h |

**Validação F1:** abrir crate grátis e paga (sem 422); upgradar skill (sem 422, nó clicável); completar 10 blocos → crate grátis creditada; ativar cada power-up e verificar efeito na partida.

### FASE 2 — Reconectar as progressões mortas 🔴
| # | Correção | Arquivo | Esforço |
|---|---|---|---|
| 2.1 | **XP de nível:** chamar `addXP(calculateWordXP(word, combo))` em `endSelection` após cada palavra encontrada (ao lado de `trackWordFound`, `game.js:2341`); tratar `leveled_up` na resposta (toast + `updateLevelUI`) | game.js | ~1h |
| 2.2 | **Season Pass:** chamar `POST /season/{username}/add-xp` com o mesmo XP da palavra (ou fração definida) no mesmo ponto; atualizar `seasonState` na resposta | game.js | ~1h |
| 2.3 | **Bônus de conquistas:** aplicar `applyAchievementBonus(points)` no cálculo de pontuação (`endSelection`, `game.js:2286-2289`); usar `getHintPrice()` em `buyHint` (`game.js:1766`) | game.js | ~1h |
| 2.4 | **Cards:** ler `total` (não `totals`) e tratar `collection_bonus` como objeto por raridade (`game.js:5154,5164-5166`); chamar `showCardPullAnimation` quando o backend enviar novo card (verificar se o evento WS de card existe — se não, disparar no `block_mined` com o card do bloco) | game.js | ~1-2h |
| 2.5 | **Energia:** ler `next_refill_at` (não `nextRefill`) para exibir o timer de recarga (`game.js:4753`); corrigir rótulo "10K SATS" → "2,000 SATS" (`index.html:256`) | game.js, index.html | ~30min |

**Validação F2:** encontrar palavras → XP sobe, nível/rank atualizam; season XP sobe e recompensa desbloqueia; bônus de conquista aparece na pontuação; hint fica mais caro/barato conforme bônus; cards exibem total/bônus corretos; timer de energia visível.

### FASE 3 — Lógica de gameplay (boss, eventos, staking) 🟠
| # | Correção | Arquivo | Esforço |
|---|---|---|---|
| 3.1 | **Boss:** chamar `resetBossState()` no caminho de derrota por timeout (antes de `prepareNextBlock` no "Tentar novamente", `game.js:3197`) e no `showBossResult(false)` (`game.js:3164`) | game.js | ~30min |
| 3.2 | **Eventos globais:** (a) ler `event_ends_at`/`event_started_at` (não `ends_at`/`started_at`) em `handleGlobalEventMessage`/`loadActiveGlobalEvent` (`game.js:5707,5741`); (b) aplicar efeitos de grade/tempo em `buildPlayableBlock` (`game.js:1878-1887`): `mempool_flood` → 15×15 + 15 s; `lightning_storm` → 8×8 + tempo base 20 s (usar o evento ativo, não só `isLightningMode`) | game.js | ~2h |
| 3.3 | **Staking:** substituir o `<select id="staking-duration">` (1/10/100 Blocks) por botões de duração 1h/6h/24h que atualizam `selectedStakeDuration` (`index.html:362-366` + `game.js:4282-4292`); remover o hardcode 6h | index.html, game.js | ~1h |
| 3.4 | **Sessão:** chamar `clearSessionState()` no encerramento da sessão (`teardownSession`, `game.js:760`) | game.js | ~15min |

**Validação F3:** forçar boss e deixar expirar → HUD some, rodada normal volta; ativar evento global (via ingestor/regtest) → grade e tempo mudam; staking com 1h/24h → duração correta no backend; F5 após encerrar → estado limpo.

### FASE 4 — CSS da migração (~97 classes de item) 🟡
Adicionar ao `pixel.css` (respeitando o tema pixel 8-bit existente — cores do `:root`, fontes `--f-pixel`/`--f-mono`, bordas 2px, sem design genérico):
| # | Bloco | Classes | Esforço |
|---|---|---|---|
| 4.1 | Feedback de jogo | `floating-text` (usar keyframe `floatUp` existente), `boss-loot-text` | ~30min |
| 4.2 | Ranking | `rank-item`, `top-1/2/3` (destaque ouro/prata/bronze) | ~30min |
| 4.3 | Missões | 12 classes (`mission-card` … `btn-claim`) | ~1h |
| 4.4 | Sprint | 13 classes (leaderboard + overlay de resultado) | ~1h |
| 4.5 | Mercado | 11 classes (listings + histórico + vazio) | ~1h |
| 4.6 | Skill Tree | 9 classes (ramos + nós + estados locked/unlocked) | ~1h |
| 4.7 | Conquistas | 10 classes (card + tooltip + progresso) | ~1h |
| 4.8 | Season | 7 classes (recompensas free/premium + estado claimed) | ~45min |
| 4.9 | Cards | 6 classes (`block-card-*` + raridades) | ~45min |
| 4.10 | Chat + Amigos | 13 classes (`chat-message-*`, `friend-*`) | ~1h |
| 4.11 | Staking + Crates | 18 classes (histórico + modal de crate + raridades) | ~1h |
| 4.12 | Keyframes + vars | 8 keyframes (`bossFlash`, `bossShake`, `bossHpDamage`, `bossIconPulse`, `bossDefeatPulse`, `halvingFlash`, `slashingFlash`, `rbfPulse`) + 3 vars (`--error-red`, `--lightning-blue`, `--warning-orange`) no `:root` | ~45min |

**Validação F4:** screenshot de cada aba (mobile 320 / tablet 768 / desktop 1440) comparando com o protótipo `prototype-pixel-final-v3.html`; **bump de `CACHE_VERSION` v18 → v19** (regra operacional: todo deploy que altera o shell exige bump).

### FASE 5 — Higiene e docs 🟢
| # | Correção | Esforço |
|---|---|---|
| 5.1 | Atualizar `docs/MECANICAS.md` com as 10 divergências do §9 (power-ups, 30 conquistas, 11 ranks, MEV +50k, 4 níveis de hardware, decaimento de halving, season trimestral, localização da loja, 11 campos de sessão) | ~1h |
| 5.2 | **Concluído:** `toggleChatPanel`/`trackPoolRank1` removidas; card pull e crate claim ativos; timer Sprint reutiliza o elemento único do HTML | concluído |
| 5.3 | Auditoria final (agents) + commit manual pelo usuário | — |

**Total estimado: ~18-22h de trabalho**, em 5 fases com health check entre cada uma.

### Riscos / decisões a tomar
1. **Power-ups (F1.4):** os efeitos exigem tocar no loop de jogo (timer, combo, slashing, sats). É a correção mais arriscada — recomendo TDD (testes de contrato) antes de implementar.
2. **XP (F2.1/2.2):** definir a fração de XP que vai para o season pass (100%? 50%?) — hoje não há definição; sugiro 100% do XP da palavra para ambos, simples e previsível.
3. **CSS (F4):** ~97 classes é volume alto; se quiser, dá para priorizar só os domínios visíveis no fluxo principal (missões, ranking, chat, cards) e deixar o resto para depois.
4. **Nada aqui altera o backend** — todas as correções são frontend (game.js/index.html/pixel.css), exceto zero. O backend está íntegro.

---

## 11. Anexos

- **Relatórios individuais dos agents** (detalhados, por aba):
  - Aba JOGO: `subagent-summary-0-20260821_112253_086016.txt` (cache de delegação)
  - Abas UPGRADES+COMPETIR: `subagent-summary-0-20260821_115515_609680.txt`
  - Abas PERFIL+SOCIAL+transversais: `subagent-summary-2-20260821_112253_091427.txt`
- **Baseline:** 7/7 containers healthy; API ready; WS 101; SW v18 ativo.
- **Nota de método:** os 3 agents rodaram em paralelo; 2 atingiram o limite de iterações após entregar o relatório (o encerramento é pós-entrega, sem perda de conteúdo); 1 (UPGRADES+COMPETIR) precisou de re-dispatch após timeout de API na primeira tentativa.



