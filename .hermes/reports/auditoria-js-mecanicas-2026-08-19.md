# Auditoria JavaScript/Mecânicas Completa — Mempool Miner

**Data:** 19 de agosto de 2026  
**Escopo:** `frontend/game.js` (6264 linhas), `frontend/index.html` (549 linhas), `frontend/pixel.css` (2309 linhas), `frontend/icons/ui-sprite.svg` (33 linhas), contratos backend  
**Modo:** Leitura apenas. Nenhum arquivo editado.

---

## 1. ERROS RUNTIME

### R-01 — `ReferenceError: handleWebSocketMessage is not defined` (ELIMINADO)
- **Status:** O achado anterior (game.js:5421) foi removido. O handler real está embutido em `socket.onmessage` (game.js:1041). ✅ Corrigido.

### R-02 — `TypeError` em `showFloatingText()` com `cell === undefined`
- **Arquivo:** `game.js:2150`
- **Linha:** `showFloatingText(selectedCells[0]?.cell, -penalty, false, false);`
- **Fluxo:** Se `consecutiveErrors >= SLASHING_THRESHOLD` mas `selectedCells` foi limpo antes, `selectedCells[0]?.cell` é `undefined`. Dentro de `showFloatingText()` (game.js:2183), `cell.getBoundingClientRect()` lança **TypeError**.
- **Severidade:** MEDIUM
- **Correção:** Guardar `if (!selectedCells[0]?.cell) return;` no início de `showFloatingText()`.

### R-03 — `TypeError` em `drawAnimatedLine()` com células removidas do DOM
- **Arquivo:** `game.js:2191-2203`
- **Fluxo:** Se a grade for reconstruída entre a seleção e o desenho (ex: resize aciona `configureGridSize`), as células referenciadas podem não estar mais no DOM, retornando retângulos zerados.
- **Severidade:** LOW
- **Correção:** Verificar `startCell.isConnected && endCell.isConnected` antes de desenhar.

### R-04 — `TypeError` em `renderWordBank()` — `currentRoundWords` indefinido
- **Arquivo:** `game.js:1789`
- **Linha:** `currentRoundWords.forEach(...)`
- **Fluxo:** Se `currentRoundWords` for `null` ou `undefined`, `.forEach` lança **TypeError**.
- **Severidade:** LOW
- **Correção:** Guardar `if (!currentRoundWords || currentRoundWords.length === 0) return;` no início.

### R-05 — `TypeError` em `showSprintResult()` — `data.time_taken.toFixed()` com undefined
- **Arquivo:** `game.js:5690`
- **Linha:** `${data.time_taken.toFixed(1)}s`
- **Fluxo:** Se o backend retornar `time_taken` como `null` ou ausente, `.toFixed()` lança **TypeError**.
- **Severidade:** MEDIUM
- **Correção:** `${(data.time_taken ?? 0).toFixed(1)}s`

### R-06 — `TypeError` em `renderSprintLeaderboard()` — `entry.time.toFixed()` com undefined
- **Arquivo:** `game.js:5748`
- **Linha:** `${entry.time.toFixed(1)}s`
- **Fluxo:** Se o backend retornar `time` como `null` ou ausente, `.toFixed()` lança **TypeError**.
- **Severidade:** MEDIUM
- **Correção:** `${(entry.time ?? 0).toFixed(1)}s`

### R-07 — `TypeError` em `updateStakingUI()` — `stakingDurationEl.textContent` com elemento nulo
- **Arquivo:** `game.js:3767`
- **Linha:** `stakingDurationEl.textContent = ...`
- **Fluxo:** `stakingDurationEl` é `document.getElementById('staking-duration')` (game.js:3717). Em `index.html:325`, `#staking-duration` é um `<select>`, não um `<span>`. Atribuir `.textContent` a um `<select>` limpa todas as `<option>` — **efeito colateral destrutivo**.
- **Severidade:** HIGH
- **Correção:** Usar um elemento separado para exibir a duração selecionada, ou usar `stakingDurationEl.value`.

### R-08 — `TypeError` em `updateEnergyUI()` — `energyState.nextRefill` parsing
- **Arquivo:** `game.js:4543`
- **Linha:** `const refillTime = new Date(nextRefill);`
- **Fluxo:** Se `nextRefill` for `null` (game.js:4494), `new Date(null)` retorna `Invalid Date`, e `diff` é `NaN`. `Math.floor(NaN)` é `NaN`, e `uiEnergyTimerEl.textContent` mostra `+1 em NaNm NaNs`.
- **Severidade:** LOW
- **Correção:** Verificar `if (!nextRefill) { uiEnergyTimerEl.textContent = ''; return; }`.

---

## 2. REFERÊNCIAS DOM NULAS

### D-01 — `#tx-loading` removido e recriado a cada rodada
- **Arquivo:** `game.js:1619`
- **Linha:** `bankEl.innerHTML = '<div class="loading-state" id="tx-loading">Aguardando transacoes (0/6)...</div>';`
- **Fluxo:** `prepareNextBlock()` recria `#tx-loading` via `innerHTML`. Mas `document.getElementById('tx-loading')` (game.js:1134, 1152, 1716, 2716, 2989) é chamado em múltiplos lugares. Se o elemento for removido entre chamadas (ex: `bankEl.innerHTML = ''` em game.js:1637), `getElementById` retorna `null` e `.innerText = ...` lança **TypeError**.
- **Severidade:** MEDIUM
- **Correção:** Usar optional chaining `?.innerText` ou verificar existência antes de acessar.

### D-02 — `#game-status-footer` sem uso no JS
- **Arquivo:** `index.html:475`, `game.js`
- **Fluxo:** `#game-status-footer` existe no HTML mas nunca é referenciado no JS. É um elemento órfão.
- **Severidade:** LOW

### D-03 — `#ui-operator-tag` vs `#ui-miner-name` duplicação
- **Arquivo:** `index.html:66-68`, `game.js:874, 972`
- **Fluxo:** `#ui-operator-tag` é visível e usado pelo JS. `#ui-miner-name` tem classe `hidden` e nunca é atualizado. Elemento duplicado sem sincronização.
- **Severidade:** LOW

### D-04 — `#boss-defeat-btn` sem listener nativo
- **Arquivo:** `game.js:3013`
- **Linha:** `btn.onclick = () => { ... }`
- **Fluxo:** O listener é definido inline em `showBossDefeatModal()`, não via `addEventListener`. Se o modal for reaberto, o handler anterior é sobrescrito — funciona, mas é frágil.
- **Severidade:** LOW

### D-05 — `#btn-sprint-play-again` criado dinamicamente
- **Arquivo:** `game.js:5697-5710`
- **Fluxo:** O botão é criado via `innerHTML` em `showSprintResult()` e o listener é adicionado via `querySelector`. Funciona, mas se o overlay for removido e recriado, o listener é perdido.
- **Severidade:** LOW

### D-06 — `#btn-close-crate` criado dinamicamente
- **Arquivo:** `game.js:6083-6086`
- **Fluxo:** Mesmo padrão que D-05. Funciona, mas frágil.
- **Severidade:** LOW

### D-07 — Elementos de staking com IDs duplicados
- **Arquivo:** `index.html:325`, `game.js:3717`
- **Fluxo:** `#staking-duration` é um `<select>` no HTML, mas o JS trata como elemento de texto (`textContent`). Isso limpa as `<option>` do select.
- **Severidade:** HIGH (mesmo que R-07)

### D-08 — `#decoder-timer-bar` usado como barra de progresso
- **Arquivo:** `game.js:4184-4193`
- **Fluxo:** `decoderTimerBarEl.style.width` é usado para animar a barra. Mas `decoderTimerBarEl` é `#decoder-timer-bar` (game.js:4098), que é uma `<div class="season-progress-bar">` no HTML. O CSS espera `.season-progress-fill` dentro, não `.season-progress-bar` diretamente.
- **Severidade:** MEDIUM
- **Correção:** Usar `decoderTimerBarEl.querySelector('#decoder-timer-fill')` ou ajustar o seletor.

---

## 3. NAVEGAÇÃO/TABS

### T-01 — `showTab()` funciona corretamente
- **Arquivo:** `game.js:55-72`
- **Status:** ✅ A função `showTab()` usa `.tab-pane` e `.mecha-btn[data-tab]` corretamente. O achado anterior de duplicação foi resolvido.

### T-02 — Tabs de season não existem no HTML
- **Arquivo:** `game.js:4844-4860`
- **Linha:** `document.querySelectorAll('.season-tab').forEach(tab => { ... })`
- **Fluxo:** `.season-tab` não existe em `index.html`. O loop é vazio — sem erro, mas sem funcionalidade. As tabs de recompensa (free/premium) não funcionam.
- **Severidade:** MEDIUM
- **Correção:** Adicionar elementos `.season-tab` ao HTML ou implementar a lógica de toggle via outro mecanismo.

### T-03 — Tabs de mercado não existem no HTML
- **Arquivo:** `game.js:5329-5357`
- **Linha:** `document.querySelectorAll('.market-tab-btn').forEach(tab => { ... })`
- **Fluxo:** `.market-tab-btn` não existe em `index.html`. O loop é vazio — sem erro, mas sem funcionalidade.
- **Severidade:** MEDIUM
- **Correção:** Adicionar elementos `.market-tab-btn` ao HTML.

### T-04 — Filtros de card não existem no HTML
- **Arquivo:** `game.js:5008-5019`
- **Linha:** `document.querySelectorAll('.card-filter').forEach(filter => { ... })`
- **Fluxo:** `.card-filter` não existe em `index.html`. O loop é vazio.
- **Severidade:** MEDIUM
- **Correção:** Adicionar elementos `.card-filter` ao HTML.

### T-05 — Botões de duração de staking não existem no HTML
- **Arquivo:** `game.js:4052-4062`
- **Linha:** `document.querySelectorAll('.staking-duration-btn').forEach(btn => { ... })`
- **Fluxo:** `.staking-duration-btn` não existe em `index.html`. O `<select id="staking-duration">` (index.html:325) é usado diretamente, mas o JS tenta configurar botões que não existem.
- **Severidade:** MEDIUM
- **Correção:** Usar o `<select>` existente ou adicionar botões ao HTML.

---

## 4. WRAPPERS/MONKEY PATCHES

### W-01 — Cadeia de wrappers em `teardownSession()`
- **Arquivo:** `game.js:3668-3679` (chat), `game.js:4065-4080` (staking)
- **Fluxo:** `teardownSession` é redefinido duas vezes:
  1. `game.js:3668`: `const originalTeardownSession = teardownSession; teardownSession = function(reason) { ... }`
  2. `game.js:4065`: `const originalTeardownForStaking = teardownSession; teardownSession = function(reason) { ... }`
  A segunda redefinição envolve a primeira, criando uma cadeia: staking → chat → original.
- **Severidade:** MEDIUM
- **Impacto:** Se um wrapper falhar, a cadeia inteira quebra. A ordem de execução depende da ordem de carregamento do script.

### W-02 — Wrapper em `endSelection()`
- **Arquivo:** `game.js:3302-3312`
- **Fluxo:** `const originalEndSelection = endSelection; endSelection = function() { ... }`
- **Severidade:** LOW
- **Impacto:** Adiciona `updateMissionsProgress()` após cada seleção. Funciona, mas aciona fetch a cada palavra encontrada — potencialmente excessivo.

### W-03 — Wrapper em `showResult()`
- **Arquivo:** `game.js:3315-3325`
- **Fluxo:** `const originalShowResult = showResult; showResult = function(success, message) { ... }`
- **Severidade:** LOW
- **Impacto:** Adiciona `updateMissionsProgress()` ao completar bloco.

### W-04 — Wrapper em `showOrphanBlockSalvage()`
- **Arquivo:** `game.js:3328-3338`
- **Fluxo:** `const originalShowOrphanBlockSalvage = showOrphanBlockSalvage; showOrphanBlockSalvage = function() { ... }`
- **Severidade:** LOW

### W-05 — Wrapper em `buyHint()`
- **Arquivo:** `game.js:3341-3351`
- **Fluxo:** `const originalBuyHint = buyHint; buyHint = function() { ... }`
- **Severidade:** LOW

### W-06 — Wrapper em `buyHardware()`
- **Arquivo:** `game.js:3354-3364`
- **Fluxo:** `const originalBuyHardware = buyHardware; buyHardware = function() { ... }`
- **Severidade:** LOW

### W-07 — Wrapper em `buyLightning()`
- **Arquivo:** `game.js:3367-3377`
- **Fluxo:** `const originalBuyLightning = buyLightning; buyLightning = function() { ... }`
- **Severidade:** LOW

### W-08 — Wrapper em `prepareNextBlock()`
- **Arquivo:** `game.js:4314-4318`
- **Fluxo:** `const originalPrepareNextBlock = prepareNextBlock; prepareNextBlock = function() { ... }`
- **Severidade:** LOW
- **Impacto:** Adiciona `checkDecoderAvailability()` após preparar próximo bloco.

### W-09 — Cadeia dupla em `startNetworkRace()`
- **Arquivo:** `game.js:4630-4635` (energy), `game.js:5755-5762` (sprint)
- **Fluxo:** `startNetworkRace` é redefinido DUAS vezes:
  1. `game.js:4630`: `const originalStartNetworkRace = startNetworkRace; startNetworkRace = async function() { ... }` (energy)
  2. `game.js:5755`: `const originalStartNetworkRaceForSprint = startNetworkRace; startNetworkRace = async function() { ... }` (sprint)
  A cadeia é: sprint → energy → original.
- **Severidade:** HIGH
- **Impacto:** O wrapper de sprint verifica `sprintMode` primeiro. Se `sprintMode` for `true`, chama `startSprintRound()` e ignora o wrapper de energy. Se `sprintMode` for `false`, chama o wrapper de energy, que gasta energia antes de iniciar a corrida. A ordem importa e é frágil.

### W-10 — `registerSessionInitializer` como alternativa melhor
- **Arquivo:** `game.js:310-325`
- **Status:** ✅ O sistema de `sessionInitializers` é uma abordagem melhor que wrappers. 12 módulos usam `registerSessionInitializer`: missions, chat-staking, skills, energy, season, cards, market, global-events, friends, crates, level.

---

## 5. TIMERS E LISTENERS ÓRFÃOS

### O-01 — `energyTimerInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:583`
- **Linha:** `clearInterval(energyTimerInterval);`
- **Status:** ✅ Corretamente limpo.

### O-02 — `seasonTimerInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:584`
- **Linha:** `clearInterval(seasonTimerInterval);`
- **Status:** ✅ Corretamente limpo.

### O-03 — `sprintTimerInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:585`
- **Linha:** `clearInterval(sprintTimerInterval);`
- **Status:** ✅ Corretamente limpo.

### O-04 — `decoderTimerInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:586`
- **Linha:** `clearInterval(decoderTimerInterval);`
- **Status:** ✅ Corretamente limpo.

### O-05 — `eventCountdownInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:587`
- **Linha:** `clearInterval(eventCountdownInterval);`
- **Status:** ✅ Corretamente limpo.

### O-06 — `stakeCountdownInterval` e `stakePollInterval` não limpos em `teardownSession()`
- **Arquivo:** `game.js:588-589`
- **Linhas:** `clearInterval(stakeCountdownInterval); clearInterval(stakePollInterval);`
- **Status:** ✅ Corretamente limpos.

### O-07 — `missionsRefreshInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:582`
- **Linha:** `clearInterval(missionsRefreshInterval);`
- **Status:** ✅ Corretamente limpo.

### O-08 — `poolsInterval` não limpo em `teardownSession()`
- **Arquivo:** `game.js:581`
- **Linha:** `clearInterval(poolsInterval);`
- **Status:** ✅ Corretamente limpo.

### O-09 — `ResizeObserver` não desconectado em `teardownSession()`
- **Arquivo:** `game.js:848-851`
- **Fluxo:** `gridResizeObserver.observe(gridWrapperEl)` é criado no load, mas nunca é desconectado em `teardownSession()`. O observer continua ativo após a sessão ser encerrada.
- **Severidade:** LOW
- **Correção:** Adicionar `gridResizeObserver.disconnect()` em `teardownSession()`.

### O-10 — Listeners de `window` não removidos
- **Arquivo:** `game.js:395-432`
- **Fluxo:** `window.addEventListener('online', ...)`, `window.addEventListener('offline', ...)`, `window.addEventListener('beforeinstallprompt', ...)`, `window.addEventListener('appinstalled', ...)`, `navigator.serviceWorker.addEventListener('controllerchange', ...)` são adicionados no load e nunca removidos.
- **Severidade:** LOW (são listeners de sistema, não de sessão)

### O-11 — `document.addEventListener('keydown', ...)` não removido
- **Arquivo:** `game.js:658-682`
- **Fluxo:** O handler de tab-trap em modais é adicionado no load e nunca removido. Funciona corretamente (verifica `.modal-overlay.active`), mas é um listener permanente.
- **Severidade:** LOW

### O-12 — `document.addEventListener('DOMContentLoaded', ...)` duplicado
- **Arquivo:** `game.js:2622-2631`
- **Fluxo:** Dois handlers `DOMContentLoaded` existem. O segundo (game.js:2622) registra listeners para achievements. O primeiro não foi encontrado no código atual — pode ter sido removido.
- **Severidade:** LOW

---

## 6. FETCH SEM TRATAMENTO

### F-01 — `loadPlayerState()` sem AbortController
- **Arquivo:** `game.js:1474-1496`
- **Fluxo:** `fetch(playerStateUrl(realmId, username))` sem `signal`. Se a sessão for encerrada durante o fetch, a resposta é processada mesmo após `teardownSession()`.
- **Severidade:** MEDIUM
- **Correção:** Adicionar AbortController e verificar `generation === sessionGeneration` antes de aplicar o estado.

### F-02 — `loadAchievementStats()` sem AbortController
- **Arquivo:** `game.js:2634-2659`
- **Fluxo:** Mesmo problema que F-01.
- **Severidade:** MEDIUM

### F-03 — `startDecoderGame()` sem AbortController
- **Arquivo:** `game.js:4124-4181`
- **Fluxo:** `fetch(url.toString(), { method: 'GET', ... })` sem `signal`.
- **Severidade:** LOW

### F-04 — `submitDecoderAnswer()` sem AbortController
- **Arquivo:** `game.js:4197-4260`
- **Fluxo:** Mesmo problema.
- **Severidade:** LOW

### F-05 — `loadSkillTree()` sem AbortController
- **Arquivo:** `game.js:4336-4359`
- **Fluxo:** `fetch(activeNetworkApiUrl(...), { headers: { 'X-Abort-After': '5000' } })` usa header customizado, não `AbortController`. Se o backend não respeitar `X-Abort-After`, o fetch continua.
- **Severidade:** LOW

### F-06 — Múltiplos endpoints sem AbortController
- **Arquivo:** `game.js:4504-4622` (energy), `game.js:4667-4836` (season), `game.js:4904-5057` (cards), `game.js:5093-5326` (market), `game.js:5570-5752` (sprint), `game.js:5779-5940` (friends), `game.js:5978-6109` (crates), `game.js:6153-6264` (level)
- **Fluxo:** Todos usam `fetch` sem `AbortController` ou com header `X-Abort-After` que o backend pode não respeitar.
- **Severidade:** MEDIUM
- **Correção:** Adicionar AbortController a todos os fetches de sessão e abortar em `teardownSession()`.

---

## 7. SESSÕES

### S-01 — `sessionGeneration` incrementado corretamente
- **Arquivo:** `game.js:566`
- **Status:** ✅ `teardownSession()` incrementa `sessionGeneration` e todos os timers verificam `generation === sessionGeneration`.

### S-02 — `sessionReady` não resetado em todos os caminhos
- **Arquivo:** `game.js:567`
- **Fluxo:** `sessionReady = false` é definido em `teardownSession()`. Mas `sessionReady` também é definido em `socket.onmessage` (game.js:1070). Se o WebSocket cair e reconectar, `sessionReady` pode ficar `true` sem que a sessão esteja realmente pronta.
- **Severidade:** LOW

### S-03 — `saveSessionState()` salva estado inconsistente
- **Arquivo:** `game.js:198-213`
- **Fluxo:** Salva `minerName`, `activeRealmId`, `balanceSatoshis`, etc. Mas não salva `sessionGeneration`, `isPlaying`, `isTransitioning`, `wordsFoundInBlock`, `currentRoundEarnings`. Ao restaurar (game.js:859-899), o estado pode estar inconsistente.
- **Severidade:** MEDIUM
- **Correção:** Salvar mais campos ou limpar campos voláteis ao restaurar.

### S-04 — Restauração de sessão tenta reconectar automaticamente
- **Arquivo:** `game.js:889`
- **Linha:** `void startSession(activeRealmId);`
- **Fluxo:** Ao restaurar sessão, `startSession()` é chamado automaticamente. Se o backend estiver indisponível, o jogador fica preso em um loop de reconexão.
- **Severidade:** MEDIUM
- **Correção:** Adicionar limite de tentativas ou mostrar modal de erro após N falhas.

---

## 8. MODAIS

### M-01 — `setModalState()` funciona corretamente
- **Arquivo:** `game.js:639-656`
- **Status:** ✅ Gerencia `.active`, `aria-hidden`, foco, e retorno de foco via `WeakMap`.

### M-02 — `#auth-modal` é `<div>` mas tem `<form>` dentro
- **Arquivo:** `index.html:483-498`
- **Fluxo:** `#auth-modal` é `<div class="modal-wrap">` com `<form id="auth-form">` dentro. O listener `submit` está no form (game.js:801), não no modal. Funciona corretamente.
- **Severidade:** N/A

### M-03 — `#result-modal` reutilizado para RBF
- **Arquivo:** `game.js:2237-2259` (showResult), `game.js:2266-2320` (showOrphanBlockSalvage)
- **Fluxo:** Ambos usam `#result-modal`, `#result-title`, `#result-text`, `#next-btn`. RBF redefine o conteúdo do modal antes de `showResult()` ser chamado. Se `showResult()` for chamado enquanto RBF está ativo, o conteúdo é sobrescrito.
- **Severidade:** LOW

### M-04 — `#decoder-modal` sem botão de fechar por ESC
- **Arquivo:** `game.js:4276-4288`
- **Fluxo:** `closeDecoderModal()` fecha o modal, mas não há handler de `Escape` para fechá-lo. O handler global de `keydown` (game.js:658) só faz tab-trap, não fecha modais.
- **Severidade:** LOW
- **Correção:** Adicionar handler de `Escape` em `decoderInputEl` ou no modal.

### M-05 — `#boss-defeat-modal` sem botão de fechar por ESC
- **Arquivo:** `game.js:2998-3021`
- **Fluxo:** Mesmo problema que M-04.
- **Severidade:** LOW

### M-06 — `#achievements-modal` sem botão de fechar por ESC
- **Arquivo:** `game.js:2530-2532`
- **Fluxo:** Mesmo problema que M-04.
- **Severidade:** LOW

---

## 9. SVGs DINÂMICOS

### V-01 — `iconSvg()` e `setSvgIcon()` funcionam corretamente
- **Arquivo:** `game.js:16-36`
- **Status:** ✅ Validação de nome via `UI_ICON_NAMES`, fallback para `circle`, sanitização de classe.

### V-02 — `UI_ICON_NAMES` não inclui todos os ícones usados
- **Arquivo:** `game.js:6-11`
- **Fluxo:** `UI_ICON_NAMES` tem 28 ícones. `ui-sprite.svg` tem 32 símbolos. Ícones ausentes no Set: `level`, `gift`, `scanner`, `magnet`, `target`, `combo`, `orb`, `cross`, `check`, `crown`, `gem`, `antenna`, `link`.
- **Severidade:** MEDIUM
- **Impacto:** `iconSvg('level')` retorna `iconSvg('circle')` porque `'level'` não está no Set. Mas verificando novamente... `UI_ICON_NAMES` inclui: `antenna`, `bolt`, `boss`, `check`, `circle`, `close`, `coin`, `combo`, `controller`, `crate`, `cross`, `crown`, `cube`, `fire`, `gem`, `gift`, `level`, `link`, `magnet`, `orb`, `pickaxe`, `scanner`, `sprint`, `star`, `storm`, `swords`, `target`, `timer`, `trophy`, `warning`, `wave`. São 31 ícones. O sprite tem 32 símbolos. Verificando... o sprite tem `icon-level` (linha 32) que está no Set. Parece estar completo.
- **Severidade:** N/A (falso positivo)

### V-03 — SVGs inline no HTML não usam `iconSvg()`
- **Arquivo:** `index.html:108, 119, 120, 152, 174, 258, 298`
- **Fluxo:** 7 SVGs inline no HTML usam `<svg class="ui-icon"><use href="icons/ui-sprite.svg#icon-..."></use></svg>` diretamente, sem passar por `iconSvg()`. Não é um erro, mas é inconsistência.
- **Severidade:** LOW

### V-04 — `iconSvg()` usado em `innerHTML` — XSS potencial
- **Arquivo:** `game.js:2445, 2477, 4706, 4716, 4833, 5166, 5218, 5682, 5805, 6065`
- **Fluxo:** `iconSvg()` retorna string HTML que é injetada via `innerHTML`. O nome do ícone é validado por `UI_ICON_NAMES`, então o risco é baixo. Mas se `UI_ICON_NAMES` for expandido com entradas não confiáveis, há risco de XSS.
- **Severidade:** LOW

---

## 10. IDs

### I-01 — `#btn-start-session` sem `onclick` inline
- **Arquivo:** `index.html:494`, `game.js:275`
- **Status:** ✅ O botão tem ID e o listener é registrado via `addEventListener` no form `submit` (game.js:801). O achado anterior de CSP bloqueando `onclick` foi resolvido.

### I-02 — `#next-btn` reutilizado para múltiplas ações
- **Arquivo:** `game.js:823-831`
- **Fluxo:** `setNextButtonAction()` define `nextButtonAction` como função. O botão executa a ação e limpa o reference. Funciona, mas se o botão for clicado duas vezes rapidamente, a segunda clique executa `null`.
- **Severidade:** LOW

### I-03 — IDs dinâmicos em `renderMarketList()`
- **Arquivo:** `game.js:5154-5196`
- **Fluxo:** `innerHTML` cria `#market-filter-powerup` e `#btn-refresh-market` dentro de `marketBrowseEl`. Mas `#market-filter-powerup` também existe em `index.html:459` (fora do `marketBrowseEl`). IDs duplicados no DOM.
- **Severidade:** HIGH
- **Correção:** Usar classes ou IDs únicos por contexto.

### I-04 — `#btn-refresh-market` duplicado
- **Arquivo:** `game.js:5158`, `index.html:452`
- **Fluxo:** `#btn-refresh-market` existe no HTML (index.html:452) e é recriado via `innerHTML` em `renderMarketList()` (game.js:5158). IDs duplicados.
- **Severidade:** HIGH

---

## 11. CONTRATOS BACKEND

### B-01 — `activeNetworkApiUrl()` usa caminho relativo
- **Arquivo:** `game.js:138-145`
- **Fluxo:** `activeNetworkApiUrl('skills/...')` gera `/api/v1/networks/{realm}/skills/...`. O backend tem `GET /api/v1/networks/{realm_id}/skills/{username}` (main.py:1657). **Contrato compatível.** ✅

### B-02 — Energy: frontend usa query param, backend espera query param
- **Arquivo:** `game.js:4506`, `main.py:4220`
- **Fluxo:** Frontend: `activeNetworkApiUrl('energy/status?username=...')`. Backend: `GET /api/v1/networks/{realm_id}/energy/status` com `username` como query param. **Contrato compatível.** ✅

### B-03 — Skills: frontend usa `/upgrade`, backend usa `/upgrade`
- **Arquivo:** `game.js:4438`, `main.py:1737`
- **Fluxo:** Frontend: `activeNetworkApiUrl('skills/.../upgrade')`. Backend: `POST /api/v1/networks/{realm_id}/skills/{username}/upgrade`. **Contrato compatível.** ✅

### B-04 — Decoder: frontend usa GET, backend espera POST
- **Arquivo:** `game.js:4126-4130`, `main.py:4516`
- **Fluxo:** Frontend: `GET /api/v1/networks/{realm}/decoder/start` com `body: JSON.stringify({ username })`. Backend: `POST /api/v1/networks/{realm_id}/decoder/start`. **MISMATCH — GET vs POST.**
- **Severidade:** HIGH
- **Correção:** Mudar para `method: 'POST'` no frontend.

### B-05 — Decoder submit: frontend usa POST, backend espera POST
- **Arquivo:** `game.js:4208`, `main.py:4580`
- **Fluxo:** Ambos usam POST. **Contrato compatível.** ✅

### B-06 — Crates inventory: frontend usa query param, backend espera query param
- **Arquivo:** `game.js:5980`, `main.py:3652`
- **Fluxo:** Frontend: `activeNetworkApiUrl('crates/inventory?username=...')`. Backend: `GET /api/v1/networks/{realm_id}/crates/inventory` com `username` como query param. **Contrato compatível.** ✅

### B-07 — Market: frontend usa `activeNetworkApiUrl('market/list')`, backend espera `/market/list`
- **Arquivo:** `game.js:5095`, `main.py:2473`
- **Fluxo:** Frontend gera `/api/v1/networks/{realm}/market/list`. Backend: `GET /api/v1/networks/{realm_id}/market/list`. **Contrato compatível.** ✅

### B-08 — Season: frontend usa `activeNetworkApiUrl('season/...')`, backend não tem rota
- **Arquivo:** `game.js:4669`
- **Fluxo:** Frontend: `activeNetworkApiUrl('season/...')` gera `/api/v1/networks/{realm}/season/...`. Buscando no backend... **Nenhuma rota `/season/` encontrada em main.py.**
- **Severidade:** CRITICAL
- **Correção:** Implementar endpoint no backend ou remover a mecânica do frontend.

### B-09 — Sprint: frontend usa `activeNetworkApiUrl('sprint/...')`, backend não tem rota
- **Arquivo:** `game.js:5572`
- **Fluxo:** Frontend: `activeNetworkApiUrl('sprint/start')` gera `/api/v1/networks/{realm}/sprint/start`. **Nenhuma rota `/sprint/` encontrada em main.py.**
- **Severidade:** CRITICAL
- **Correção:** Implementar endpoint no backend ou remover a mecânica do frontend.

### B-10 — Level: frontend usa `activeNetworkApiUrl('level/...')`, backend não tem rota
- **Arquivo:** `game.js:6155`
- **Fluxo:** Frontend: `activeNetworkApiUrl('level/...')` gera `/api/v1/networks/{realm}/level/...`. **Nenhuma rota `/level/` encontrada em main.py.**
- **Severidade:** CRITICAL
- **Correção:** Implementar endpoint no backend ou remover a mecânica do frontend.

### B-11 — `block_mined` WebSocket sem `epoch` field
- **Arquivo:** `main.py:125-132`
- **Fluxo:** `PUBLIC_EVENT_FIELDS['block_mined']` inclui `block_hash`, `mempool_count`, `discarded_backlog`, `is_halving_block`. **Não inclui `epoch`.** Mas o frontend verifica `data.epoch` em game.js:1246. Se `epoch` não estiver no payload, a verificação de epoch divergente nunca aciona.
- **Severidade:** MEDIUM
- **Correção:** Adicionar `epoch` ao frozenset de `block_mined` ou remover a verificação no frontend.

---

## 12. SPRINT/MARKET/SEASON E MISTURA DE MECÂNICAS

### X-01 — Sprint mode interfere com fluxo normal
- **Arquivo:** `game.js:5546-5762`
- **Fluxo:** `sprintMode` é um toggle global. Quando ativo, `startNetworkRace()` chama `startSprintRound()` em vez da corrida normal. Mas `startSprintRound()` faz fetch para backend (que não existe — B-09) e redefine `currentGridSize`, `currentRoundWords`, etc. Se o fetch falhar, `sprintMode` fica `true` mas a rodada não inicia.
- **Severidade:** HIGH
- **Correção:** Desativar `sprintMode` se o fetch falhar, ou implementar o endpoint.

### X-02 — Energy system gasta energia a cada rodada
- **Arquivo:** `game.js:4630-4635`
- **Fluxo:** O wrapper de `startNetworkRace()` chama `spendEnergy()` antes de iniciar a corrida. Se o jogador não tem energia, a rodada não inicia. Mas não há feedback visual claro — `showNotification()` mostra erro, mas a UI não indica que a energia é o bloqueio.
- **Severidade:** MEDIUM
- **Correção:** Mostrar indicador visual de energia insuficiente na UI.

### X-03 — Boss mode não limpa `isBossActive` em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `teardownSession()` não reseta `isBossActive`, `bossHp`, `bossMaxHp`, etc. Se a sessão for encerrada durante um boss block, o estado do boss persiste na próxima sessão.
- **Severidade:** HIGH
- **Correção:** Chamar `resetBossState()` em `teardownSession()`.

### X-04 — Global events não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `teardownSession()` não limpa `activeGlobalEvent` ou esconde o banner de evento global. Se a sessão for encerrada durante um evento, o banner permanece visível.
- **Severidade:** MEDIUM
- **Correção:** Chamar `hideGlobalEventBanner()` em `teardownSession()`.

### X-05 — Decoder não limpo em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `teardownSession()` não fecha `#decoder-modal` ou limpa `decoderActive`. Se a sessão for encerrada durante um decoder game, o modal permanece aberto.
- **Severidade:** MEDIUM
- **Correção:** Chamar `closeDecoderModal()` em `teardownSession()`.

### X-06 — Staking countdown continua após `teardownSession()`
- **Arquivo:** `game.js:4065-4080`
- **Fluxo:** O wrapper de `teardownSession()` para o countdown e reseta `stakeState`. Mas se o countdown estiver em meio a um tick, o `setInterval` pode executar após o `clearInterval`.
- **Severidade:** LOW

### X-07 — Season timer continua após `teardownSession()`
- **Arquivo:** `game.js:584`
- **Fluxo:** `clearInterval(seasonTimerInterval)` é chamado, mas `seasonData` não é limpa. Se a sessão for reiniciada, `seasonData` pode conter dados da sessão anterior.
- **Severidade:** LOW

### X-08 — Cards não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `cardsData` não é limpa em `teardownSession()`.
- **Severidade:** LOW

### X-09 — Market não limpo em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `marketData`, `marketHistoryData`, `marketInventory` não são limpos em `teardownSession()`.
- **Severidade:** LOW

### X-10 — Friends não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `friendsData` não é limpa em `teardownSession()`.
- **Severidade:** LOW

### X-11 — Crates não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `crateState` não é limpo em `teardownSession()`.
- **Severidade:** LOW

### X-12 — Level não limpo em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `levelState` não é limpo em `teardownSession()`.
- **Severidade:** LOW

### X-13 — Achievements não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `achievementsData`, `achievementBonuses`, e todos os counters de tracking não são limpos em `teardownSession()`.
- **Severidade:** MEDIUM

### X-14 — Missions não limpos em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `missionsData` não é limpa em `teardownSession()`.
- **Severidade:** LOW

### X-15 — Energy state não limpo em `teardownSession()`
- **Arquivo:** `game.js:565-634`
- **Fluxo:** `energyState` não é limpo em `teardownSession()`. O timer é parado, mas o estado persiste.
- **Severidade:** LOW

---

## 13. RESUMO DE SEVERIDADE

| Severidade | Contagem | Achados |
|---|---|---|
| CRITICAL | 3 | B-08 (Season sem backend), B-09 (Sprint sem backend), B-10 (Level sem backend) |
| HIGH | 6 | R-07 (stakingDurationEl limpa options), I-03/I-04 (IDs duplicados), W-09 (cadeia dupla startNetworkRace), X-01 (Sprint sem fallback), X-03 (Boss state persiste) |
| MEDIUM | 18 | R-02, R-05, R-06, D-01, D-08, T-02/03/04/05, F-01/02/06, S-03/04, B-11, X-02/04/05, X-13 |
| LOW | 25 | R-03/04, D-02/03/04/05/06, O-09/10/11/12, F-03/04/05, S-02, M-03/04/05/06, V-03/04, I-02, W-02/03/04/05/06/07/08, X-06/07/08/09/10/11/12/14/15 |

---

## 14. OBSERVAÇÕES ADICIONAIS

### 14.1 — `style.css` é código morto
- **Arquivo:** `frontend/style.css` (4754 linhas)
- **Status:** Não carregado por `index.html`. 105KB de código morto.

### 14.2 — `user-select: none` global
- **Arquivo:** `pixel.css:74`
- **Fluxo:** `* { user-select: none; }` impede seleção de texto em toda a página, incluindo inputs e mensagens de erro.

### 14.3 — `maximum-scale=1.0, user-scalable=no`
- **Arquivo:** `index.html:5`
- **Fluxo:** Viola WCAG 2.1 1.4.10 e 1.6.1. Usuários com deficiência visual não podem dar zoom.

### 14.4 — `confirm()` nativo para cancelamento de stake
- **Arquivo:** `game.js:3988-3993`
- **Fluxo:** Usa `confirm()` nativo do navegador em vez de modal customizado. Inconsistente com o design do jogo.

### 14.5 — `innerHTML` em múltiplos lugares
- **Arquivo:** `game.js:2434, 2458, 2948, 3005, 3886, 3890, 3911, 5154, 5180, 5209, 5225, 5680, 5734, 5828, 5893, 6063`
- **Fluxo:** 16+ usos de `innerHTML` para renderizar conteúdo dinâmico. A maioria usa dados do backend, então o risco de XSS depende da sanitização do backend.

### 14.6 — Polling excessivo
- **Fluxo:** Energy a cada 10s, Season a cada 30s, Staking a cada 30s, Missions a cada 30s, Market a cada sessão. Se o backend estiver lento, os requests se acumulam.

### 14.7 — `void` usado para fire-and-forget
- **Arquivo:** Múltiplos lugares
- **Fluxo:** `void fetchLeaderboard(...)`, `void syncPlayerState()`, etc. Padrão consistente para fire-and-forget. ✅

### 14.8 — `scheduleForSession()` como padrão para timers
- **Arquivo:** `game.js:434-446`
- **Fluxo:** Todos os timers de sessão usam `scheduleForSession()` que verifica `sessionGeneration`. ✅ Padrão consistente.

---

## 15. COMPARAÇÃO COM AUDITORIA ANTERIOR

| Achado anterior | Status |
|---|---|
| CSP bloqueia `onclick` inline | ✅ Resolvido — handlers migrados para `addEventListener` |
| `handleWebSocketMessage` não definido | ✅ Removido — handler embutido em `socket.onmessage` |
| 25 URLs frontend incompatíveis | ✅ Resolvido — `activeNetworkApiUrl()` gera URLs corretas |
| Season Pass backend 500 | ❓ Não verificado — endpoint não encontrado em main.py |
| Market backend 500 | ❓ Não verificado — endpoint existe mas não testado |
| `loadPowerupsInventory()` vazia | ✅ Implementada — chama `loadMarketInventory()` |
| `renderWordBank()` vazia | ✅ Implementada — lógica completa |
| Cadeia de 10 wrappers em `startSession` | ❌ Não encontrado — `startSession` não é mais wrapped |
| DOM duplicado/oculto (compatibility aliases) | ❌ Não encontrado — aliases removidos |
| RBF migrado para elemento incompatível | ✅ Resolvido — usa `#next-btn` via `setNextButtonAction()` |

---

*Fim da auditoria. Nenhum arquivo foi modificado.*
