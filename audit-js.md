# Audit JavaScript — `frontend/game.js`

> Arquivo: `frontend/game.js` — 6053 linhas, ~215KB

> HTML de referência: `frontend/index.html`

---

## 1. Funções declaradas mas nunca chamadas

- **Linha 141**: `clearSessionState` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 2348**: `trackPoolRank1` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 2354**: `getHintPrice` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 2360**: `applyAchievementBonus` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 4789**: `showCardPullAnimation` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 5499**: `loadSprintLeaderboard` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 6000**: `addXP` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.
- **Linha 6041**: `calculateWordXP` — declarada mas nunca chamada. **Impacto: baixo**. Sugestão: Remover ou verificar se deveria ser invocada.

## 2. Variáveis declaradas mas nunca usadas

- **Linha 644**: `eventPreannounceTimeout` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 1930**: `rect` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 2454**: `originalWordsPerBlock` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 2774**: `missionsPanelEl` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 3136**: `CHAT_EMOJIS` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 4059**: `skillsHeaderEl` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 4839**: `marketSellEl` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.
- **Linha 4842**: `btnRefreshMarketEl` — declarada mas nunca usada. **Impacto: baixo**. Sugestão: Remover.

## 3. Event listeners duplicados no mesmo elemento

- **Linha 3790**: `addEventListener("click")` em `btn` duplicado (original na linha 2191). **Impacto: médio**. Sugestão: Consolidar handlers.
- **Linha 4513**: `addEventListener("click")` em `claimBtn` duplicado (original na linha 2923). **Impacto: médio**. Sugestão: Consolidar handlers.
- **Linha 4963**: `addEventListener("click")` em `btn` duplicado (original na linha 2191). **Impacto: médio**. Sugestão: Consolidar handlers.
- **Linha 5100**: `addEventListener("click")` em `tab` duplicado (original na linha 4588). **Impacto: médio**. Sugestão: Consolidar handlers.

## 4. Memory leaks (intervals/timeouts não limpos)

- **Linha 1809**: `setTimeout(() => bossHpBar.classList.remove('boss-hp-damage'), 300)` — timeout inline sem variável de referência para limpeza no teardown. **Impacto: baixo**.
- **Linha 1813**: `setTimeout(() => document.body.classList.remove('boss-shake'), 500)` — mesmo problema. **Impacto: baixo**.
- **Linha 1902**: `setTimeout(() => document.body.classList.remove('slashing-flash'), 600)` — mesmo problema. **Impacto: baixo**.
- **Linha 2436**: `setTimeout(() => document.body.classList.remove('boss-flash'), 1500)` — mesmo problema. **Impacto: baixo**.
- **Linha 2438**: `setTimeout(() => document.body.classList.remove('boss-shake'), 500)` — mesmo problema. **Impacto: baixo**.
- **Linha 4815**: `setTimeout(() => { overlay.classList.add('hidden'); overlay.remove(); }, 3000)` — card pull animation sem limpeza no teardown. **Impacto: baixo**.
- **Linha 5877**: `setTimeout(() => { crateIcon.classList.add('revealed'); }, 500)` — crate animation sem limpeza. **Impacto: baixo**.
- **Linha 6029**: `setTimeout(() => levelValueEl.classList.remove('leveled-up'), 600)` — level-up animation sem limpeza. **Impacto: baixo**.
- **Linha 973**: `setTimeout(() => document.body.classList.remove('halving-flash'), 2000)` — halving flash sem limpeza. **Impacto: baixo**.
- **Linha 1071**: `setTimeout(() => { ... startSession(activeRealmId); }, 1000)` — reconexão por epoch divergente sem limpeza no teardown. **Impacto: médio**. Sugestão: Usar `scheduleForSession` para vincular ao ciclo de vida da sessão.

## 5. Elementos DOM referenciados que não existem no HTML

- **Linha 4063**: `getElementById("skills-content")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 4218**: `getElementById("btn-skills")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 4606**: `getElementById("btn-season")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 4776**: `getElementById("btn-cards")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 4999**: `getElementById("market-sell-select")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5042**: `getElementById("market-sell-price")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5059**: `getElementById("btn-market-sell")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5136**: `getElementById("btn-market")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5392**: `getElementById("sprint-timer-display")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5405**: `getElementById("sprint-timer-value")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5516**: `getElementById("sprint-leaderboard-list")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5740**: `getElementById("btn-friends")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.
- **Linha 5876**: `getElementById("crate-icon")` — elemento **não existe** no HTML. **Impacto: crítico**. Sugestão: Adicionar ao HTML ou remover referência.

## 6. Fetch calls sem tratamento de erro adequado

- **Linha 386**: `const response = await fetch(NETWORKS_URL, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 1098**: `const response = await fetch(url, { signal: controller.signal });` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 1134**: `const response = await fetch(leaderboardUrl(realmId), { signal: controller.signa` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 1190**: `const response = await fetch(url, { signal: controller.signal });` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 1234**: `const response = await fetch(leaderboardUrl(realmId), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 1263**: `await fetch(playerStateUrl(realmId, minerName), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 2381**: `const response = await fetch(achievementsUrl(realmId, username));` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 2999**: `const response = await fetch(updateMissionsUrl(activeRealmId, minerName), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 3586**: `const response = await fetch(stakingStatusUrl(activeRealmId, minerName));` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 3674**: `const response = await fetch(stakingStakeUrl(activeRealmId), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 3735**: `const response = await fetch(stakingUnstakeUrl(activeRealmId), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 3945**: `const response = await fetch(url.toString(), {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 4168**: `const response = await fetch(`/api/${realmId}/skills/${encodeURIComponent(minerN` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 4310**: `const response = await fetch(`/api/${realmId}/energy/spend/${encodeURIComponent(` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 4341**: `const response = await fetch(`/api/${realmId}/energy/buy/${encodeURIComponent(mi` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 4524**: `const response = await fetch(`/api/${realmId}/season/${encodeURIComponent(minerN` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5016**: `const response = await fetch(`/api/${realmId}/market/buy`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5066**: `const response = await fetch(`/api/${realmId}/market/sell`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5293**: `const response = await fetch(`/api/${realmId}/global-events`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5357**: `const response = await fetch(`/api/${realmId}/sprint/start`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5442**: `const response = await fetch(`/api/${realmId}/sprint/submit`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5670**: `const response = await fetch(`/api/${realmId}/friends/add`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5820**: `const response = await fetch(`/api/${realmId}/crates/open`, {` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 5941**: `const response = await fetch(`/api/${realmId}/level/${encodeURIComponent(minerNa` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.
- **Linha 6002**: `const response = await fetch(`/api/${realmId}/level/${encodeURIComponent(minerNa` — sem try/catch. **Impacto: médio**. Sugestão: Envolver em try/catch.

## 7. Código duplicado entre funções

- **Padrão de monkey-patching (23 ocorrências)**: Múltiplas funções são sobrescritas com wrappers que chamam a original e adicionam comportamento extra. **Impacto: médio**. Sugestão: Substituir por sistema de hooks/observers centralizado.

  - **Linha 2454**: `const originalWordsPerBlock = WORDS_PER_BLOCK;`
  - **Linha 3029**: `const originalStartSession = startSession;`
  - **Linha 3050**: `const originalEndSelection = endSelection;`
  - **Linha 3063**: `const originalShowResult = showResult;`
  - **Linha 3076**: `const originalShowOrphanBlockSalvage = showOrphanBlockSalvage;`
  - **Linha 3089**: `const originalBuyHint = buyHint;`
  - **Linha 3102**: `const originalBuyHardware = buyHardware;`
  - **Linha 3115**: `const originalBuyLightning = buyLightning;`
  - **Linha 3402**: `const originalTeardownSession = teardownSession;`
  - **Linha 3416**: `const originalStartSessionWrapped = startSession;`
  - **Linha 3802**: `const originalTeardownForStaking = teardownSession;`
  - **Linha 4044**: `const originalPrepareNextBlock = prepareNextBlock;`
  - **Linha 4371**: `const originalStartNetworkRace = startNetworkRace;`
  - **Linha 4379**: `const originalStartSessionForEnergy = startSession;`
  - **Linha 4628**: `const originalStartSessionForSeason = startSession;`
  - **Linha 4822**: `const originalStartSessionForCards = startSession;`
  - **Linha 5150**: `const originalStartSessionForMarket = startSession;`
  - **Linha 5311**: `const originalHandleWebSocketMessage = handleWebSocketMessage;`
  - **Linha 5322**: `const originalStartSessionForGlobalEvents = startSession;`
  - **Linha 5540**: `const originalStartNetworkRaceForSprint = startNetworkRace;`
  - **Linha 5753**: `const originalStartSessionForFriends = startSession;`
  - **Linha 5911**: `const originalStartSessionForCrates = startSession;`
  - **Linha 6048**: `const originalStartSessionForLevel = startSession;`

- **Linha 1475-1485 e Linha 2563-2577**: Código de construção de grid duplicado entre `buildPlayableBlock` e `buildBossPlayableBlock`. **Impacto: baixo**. Sugestão: Extrair em função `buildGrid(size)` compartilhada.
- **Linha 1502-1508 e Linha 2615-2626**: Preenchimento de caracteres aleatórios duplicado. **Impacto: baixo**. Sugestão: Extrair em função `fillRandomChars()`.
- **Linha 1956-1979 e Linha 2637-2673**: Lógica de timer duplicada entre `startNetworkRace` e `startBossNetworkRace`. **Impacto: baixo**. Sugestão: Extrair em função `startTimer(duration, options)`.
- **Linha 1984-2003 e Linha 2678-2703**: Lógica de modal de resultado duplicada entre `showResult` e `showBossResult`. **Impacto: baixo**. Sugestão: Extrair em função `showModalResult(title, text, color, btnText)`.

## 8. Funções muito longas (>100 linhas)

- **Linha 740**: `startSession` — ~340 linhas. **Impacto: médio**. Sugestão: Dividir em subfunções com responsabilidades únicas.
- **Linha 1775**: `endSelection` — ~133 linhas. **Impacto: médio**. Sugestão: Dividir em subfunções com responsabilidades únicas.

## 9. Variáveis globais poluídas

- **114 variáveis globais** declaradas com `let` no escopo raiz. **Impacto: médio**. Sugestão: Encapsular estado em um objeto namespace ou módulo IIFE.

Variáveis globais:
  - `audioContext` (linha 5)
  - `currentGridSize` (linha 85)
  - `ws` (linha 86)
  - `grid` (linha 87)
  - `txBuffer` (linha 88)
  - `blockWords` (linha 89)
  - `selectedCells` (linha 90)
  - `isSelecting` (linha 91)
  - `isPlaying` (linha 92)
  - `isTransitioning` (linha 93)
  - `isLightningMode` (linha 94)
  - `activeRealmId` (linha 95)
  - `activeEpoch` (linha 96)
  - `sessionGeneration` (linha 97)
  - `sessionReady` (linha 98)
  - `networkCatalog` (linha 99)
  - `catalogRetryTimeout` (linha 100)
  - `reconnectTimeout` (linha 101)
  - `leaderboardRequestController` (linha 104)
  - `networkHealthRequestController` (linha 105)
  - `networkCatalogRequestController` (linha 106)
  - `activePointerId` (linha 107)
  - `deferredInstallPrompt` (linha 108)
  - `serviceWorkerRegistration` (linha 109)
  - `reloadingForUpdate` (linha 110)
  - `minerName` (linha 146)
  - `balanceSatoshis` (linha 147)
  - `hardwareLevel` (linha 148)
  - `hardwareNames` (linha 149)
  - `hardwarePrices` (linha 150)
  - `networkTimeBonus` (linha 151)
  - `roundNumber` (linha 155)
  - `baseReward` (linha 156)
  - `effectiveBaseReward` (linha 157)
  - `wordsFoundInBlock` (linha 158)
  - `consecutiveErrors` (linha 161)
  - `networkTimeLimit` (linha 165)
  - `networkTimePassed` (linha 166)
  - `networkInterval` (linha 167)
  - `leaderboardInterval` (linha 168)
  - `networkHealthInterval` (linha 169)
  - `pendingBuildTimeout` (linha 170)
  - `lastFoundTime` (linha 171)
  - `comboMultiplier` (linha 172)
  - `lightningBlocksRemaining` (linha 175)
  - `isRbfMode` (linha 624)
  - `isBossActive` (linha 629)
  - `bossHp` (linha 630)
  - `bossMaxHp` (linha 631)
  - `bossRewardMultiplier` (linha 632)
  - `bossLoot` (linha 633)
  - `bossWordsRequired` (linha 634)
  - `bossTimer` (linha 635)
  - `bossDefeatHandled` (linha 636)
  - `activeGlobalEvent` (linha 641)
  - `eventBannerEl` (linha 642)
  - `eventCountdownInterval` (linha 643)
  - `eventPreannounceTimeout` (linha 644)
  - `poolsRequestController` (linha 1176)
  - `poolsInterval` (linha 1177)
  - `rbfTimeout` (linha 2008)
  - `achievementsData` (linha 2071)
  - `achievementsFilter` (linha 2072)
  - `achievementBonuses` (linha 2073)
  - `realmsPlayed` (linha 2074)
  - `epochsSurvived` (linha 2075)
  - `scoresSubmitted` (linha 2076)
  - `bestRank` (linha 2077)
  - `poolRank1` (linha 2078)
  - `wordsFoundTotal` (linha 2079)
  - `goldenFoundTotal` (linha 2080)
  - `highFeeFoundTotal` (linha 2081)
  - `mevFoundTotal` (linha 2082)
  - `combos2xTotal` (linha 2083)
  - `combos4xTotal` (linha 2084)
  - `fastFindsTotal` (linha 2085)
  - `ultraFastFindsTotal` (linha 2086)
  - `blocksCompletedTotal` (linha 2087)
  - `maxScoreTotal` (linha 2088)
  - `poolJoinedTotal` (linha 2089)
  - `lastWordFoundTime` (linha 2090)
  - `achievementToastTimeout` (linha 2091)
  - `missionsData` (linha 2770)
  - `missionsRefreshInterval` (linha 2771)
  - `chatPanelVisible` (linha 3132)
  - `chatMessages` (linha 3133)
  - `stakeState` (linha 3435)
  - `stakeCountdownInterval` (linha 3444)
  - `stakePollInterval` (linha 3445)
  - `selectedStakeDuration` (linha 3446)
  - `decoderTimerInterval` (linha 3824)
  - `decoderTimeRemaining` (linha 3825)
  - `decoderActive` (linha 3826)
  - `decoderCooldownRemaining` (linha 3827)
  - `skillTreeData` (linha 4054)
  - `skillTreeLoading` (linha 4055)
  - `energyState` (linha 4235)
  - `energyTimerInterval` (linha 4236)
  - `seasonData` (linha 4390)
  - `seasonTimerInterval` (linha 4391)
  - `currentSeasonTab` (linha 4392)
  - `cardsData` (linha 4639)
  - `currentCardFilter` (linha 4640)
  - `marketData` (linha 4832)
  - `marketHistoryData` (linha 4833)
  - `marketInventory` (linha 4834)
  - `sprintMode` (linha 5332)
  - `sprintTimerInterval` (linha 5333)
  - `sprintTimeLeft` (linha 5334)
  - `sprintWordsFound` (linha 5335)
  - `sprintStartTime` (linha 5336)
  - `friendsData` (linha 5553)
  - `crateState` (linha 5763)
  - `levelState` (linha 5921)

## 10. Promises não awaitadas

- **Linha 241**: Chamada de `registerPwa` sem await/void: `async function registerPwa() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 363**: Chamada de `loadNetworkCatalog` sem await/void: `async function loadNetworkCatalog() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 740**: Chamada de `startSession` sem await/void: `async function startSession(realmIdOverride = null) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 845**: Chamada de `startSession` sem await/void: `startSession(activeRealmId);`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1073**: Chamada de `startSession` sem await/void: `startSession(activeRealmId);`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1084**: Chamada de `pollNetworkHealth` sem await/void: `async function pollNetworkHealth(realmId, generation) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1124**: Chamada de `fetchLeaderboard` sem await/void: `async function fetchLeaderboard(realmId = activeRealmId, generation = sessionGen`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1179**: Chamada de `fetchPools` sem await/void: `async function fetchPools(realmId = activeRealmId, generation = sessionGeneratio`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1227**: Chamada de `submitScore` sem await/void: `async function submitScore() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1256**: Chamada de `syncPlayerState` sem await/void: `async function syncPlayerState() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1286**: Chamada de `loadPlayerState` sem await/void: `async function loadPlayerState(realmId, username) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1349**: Chamada de `submitScore` sem await/void: `updateStoreUI(); submitScore();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1368**: Chamada de `submitScore` sem await/void: `hardwareLevel++; updateStoreUI(); submitScore();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1387**: Chamada de `submitScore` sem await/void: `updateStoreUI(); submitScore();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1866**: Chamada de `submitScore` sem await/void: `updateStoreUI(); submitScore();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 1975**: Chamada de `submitScore` sem await/void: `clearInterval(networkInterval); isPlaying = false; playSound('orphan'); submitSc`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2104**: Chamada de `fetchAchievements` sem await/void: `async function fetchAchievements(realmId = activeRealmId, username = minerName) `. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2119**: Chamada de `pushStats` sem await/void: `async function pushStats(statsObj) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2294**: Chamada de `pushStats` sem await/void: `pushStats({`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2307**: Chamada de `pushStats` sem await/void: `pushStats({ combos_4x: combos4xTotal });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2311**: Chamada de `pushStats` sem await/void: `pushStats({ combos_2x: combos2xTotal });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2317**: Chamada de `pushStats` sem await/void: `pushStats({ blocks_completed: blocksCompletedTotal });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2323**: Chamada de `pushStats` sem await/void: `pushStats({ realms_played: realmsPlayed.size });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2330**: Chamada de `pushStats` sem await/void: `pushStats({ scores_submitted: scoresSubmitted, max_score: maxScoreTotal });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2335**: Chamada de `pushStats` sem await/void: `pushStats({ pool_joined: poolJoinedTotal });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2340**: Chamada de `pushStats` sem await/void: `pushStats({ best_rank: bestRank });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2345**: Chamada de `pushStats` sem await/void: `pushStats({ epochs_survived: epochsSurvived });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2350**: Chamada de `pushStats` sem await/void: `pushStats({ pool_rank_1: poolRank1 });`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2378**: Chamada de `loadAchievementStats` sem await/void: `async function loadAchievementStats(realmId, username) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2668**: Chamada de `submitScore` sem await/void: `submitScore();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2814**: Chamada de `loadMissions` sem await/void: `async function loadMissions(realmId = activeRealmId, username = minerName) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2939**: Chamada de `claimReward` sem await/void: `async function claimReward(mission) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 2995**: Chamada de `updateMissionsProgress` sem await/void: `async function updateMissionsProgress() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3180**: Chamada de `loadChatHistory` sem await/void: `async function loadChatHistory() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3307**: Chamada de `sendChatMessage` sem await/void: `async function sendChatMessage() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3385**: Chamada de `sendChatMessage` sem await/void: `sendChatMessage();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3582**: Chamada de `loadStakingStatus` sem await/void: `async function loadStakingStatus() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3612**: Chamada de `loadStakingHistory` sem await/void: `async function loadStakingHistory() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3663**: Chamada de `performStake` sem await/void: `async function performStake() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3720**: Chamada de `cancelStake` sem await/void: `async function cancelStake() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3856**: Chamada de `startDecoderGame` sem await/void: `async function startDecoderGame() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 3934**: Chamada de `submitDecoderAnswer` sem await/void: `async function submitDecoderAnswer() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4038**: Chamada de `submitDecoderAnswer` sem await/void: `submitDecoderAnswer();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4066**: Chamada de `loadSkillTree` sem await/void: `async function loadSkillTree() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4164**: Chamada de `unlockSkill` sem await/void: `async function unlockSkill(branchKey, level) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4225**: Chamada de `loadSkillTree` sem await/void: `loadSkillTree();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4245**: Chamada de `loadEnergyState` sem await/void: `async function loadEnergyState() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4308**: Chamada de `spendEnergy` sem await/void: `async function spendEnergy() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4334**: Chamada de `buyEnergy` sem await/void: `async function buyEnergy() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4410**: Chamada de `loadSeasonData` sem await/void: `async function loadSeasonData() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4522**: Chamada de `claimSeasonReward` sem await/void: `async function claimSeasonReward(level) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4547**: Chamada de `buySeasonPremium` sem await/void: `async function buySeasonPremium() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4613**: Chamada de `loadSeasonData` sem await/void: `loadSeasonData();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4662**: Chamada de `loadCardsData` sem await/void: `async function loadCardsData() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4783**: Chamada de `loadCardsData` sem await/void: `loadCardsData();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4862**: Chamada de `loadMarketList` sem await/void: `async function loadMarketList() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4878**: Chamada de `loadMarketHistory` sem await/void: `async function loadMarketHistory() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 4894**: Chamada de `loadMarketInventory` sem await/void: `async function loadMarketInventory() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5014**: Chamada de `buyMarketListing` sem await/void: `async function buyMarketListing(listingId, price) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5040**: Chamada de `sellMarketPowerup` sem await/void: `async function sellMarketPowerup() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5123**: Chamada de `loadMarketList` sem await/void: `if (tab.id === 'tab-browse') loadMarketList();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5124**: Chamada de `loadMarketHistory` sem await/void: `else if (tab.id === 'tab-history') loadMarketHistory();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5125**: Chamada de `loadMarketInventory` sem await/void: `else if (tab.id === 'tab-sell') loadMarketInventory();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5143**: Chamada de `loadMarketList` sem await/void: `loadMarketList();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5144**: Chamada de `loadMarketInventory` sem await/void: `loadMarketInventory();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5291**: Chamada de `loadActiveGlobalEvent` sem await/void: `async function loadActiveGlobalEvent() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5355**: Chamada de `startSprintRound` sem await/void: `async function startSprintRound() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5436**: Chamada de `submitSprintResult` sem await/void: `submitSprintResult(sprintWordsFound, timeTaken);`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5440**: Chamada de `submitSprintResult` sem await/void: `async function submitSprintResult(wordsFound, timeTaken) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5493**: Chamada de `startSprintRound` sem await/void: `startSprintRound();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5499**: Chamada de `loadSprintLeaderboard` sem await/void: `async function loadSprintLeaderboard() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5564**: Chamada de `loadFriendsList` sem await/void: `async function loadFriendsList() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5651**: Chamada de `addFriend` sem await/void: `async function addFriend() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5702**: Chamada de `removeFriend` sem await/void: `async function removeFriend(friendUsername) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5734**: Chamada de `addFriend` sem await/void: `addFriend();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5747**: Chamada de `loadFriendsList` sem await/void: `loadFriendsList();`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5777**: Chamada de `loadCrateInventory` sem await/void: `async function loadCrateInventory() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5818**: Chamada de `openCrate` sem await/void: `async function openCrate(isFree = true) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 5939**: Chamada de `loadLevelState` sem await/void: `async function loadLevelState() {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.
- **Linha 6000**: Chamada de `addXP` sem await/void: `async function addXP(xpAmount) {`. **Impacto: baixo**. Sugestão: Adicionar `void` ou `await`.

## 11. Callbacks aninhados demais

- **17 linhas com indentação profunda (6+ níveis)** no bloco `socket.onmessage` (linhas 855-1078). **Impacto: baixo**. Sugestão: Extrair handlers de cada `data.action` em funções separadas.

  - **Linha 845** (24 espaços): `startSession(activeRealmId);`
  - **Linha 950** (24 espaços): `cancelSessionTimeout(pendingBuildTimeout);`
  - **Linha 951** (24 espaços): `pendingBuildTimeout = scheduleForSession(() => {`
  - **Linha 952** (28 espaços): `pendingBuildTimeout = undefined;`
  - **Linha 953** (28 espaços): `buildPlayableBlock();`

## 12. Estado inconsistente entre funções

- **Uso de `realmId` não declarada em template strings** (25 ocorrências a partir de linha ~4074). **Impacto: crítico**. A variável `realmId` não existe no escopo global — deveria ser `activeRealmId`. Isso causa `ReferenceError` em tempo de execução.

  - **Linha 4074**: `const response = await fetch(`/api/${realmId}/skills/${encodeURIComponent(minerN`
  - **Linha 4168**: `const response = await fetch(`/api/${realmId}/skills/${encodeURIComponent(minerN`
  - **Linha 4247**: `const response = await fetch(`/api/${realmId}/energy/status/${encodeURIComponent`
  - **Linha 4310**: `const response = await fetch(`/api/${realmId}/energy/spend/${encodeURIComponent(`
  - **Linha 4341**: `const response = await fetch(`/api/${realmId}/energy/buy/${encodeURIComponent(mi`
  - **Linha 4412**: `const response = await fetch(`/api/${realmId}/season/${encodeURIComponent(minerN`
  - **Linha 4524**: `const response = await fetch(`/api/${realmId}/season/${encodeURIComponent(minerN`
  - **Linha 4554**: `const response = await fetch(`/api/${realmId}/season/${encodeURIComponent(minerN`
  - **Linha 4664**: `const response = await fetch(`/api/${realmId}/cards/${encodeURIComponent(minerNa`
  - **Linha 4864**: `const response = await fetch(`/api/${realmId}/market/list`, {`
  - **Linha 4880**: `const response = await fetch(`/api/${realmId}/market/history`, {`
  - **Linha 4896**: `const response = await fetch(`/api/${realmId}/powerups/${encodeURIComponent(mine`
  - **Linha 5016**: `const response = await fetch(`/api/${realmId}/market/buy`, {`
  - **Linha 5066**: `const response = await fetch(`/api/${realmId}/market/sell`, {`
  - **Linha 5293**: `const response = await fetch(`/api/${realmId}/global-events`, {`
  - **Linha 5357**: `const response = await fetch(`/api/${realmId}/sprint/start`, {`
  - **Linha 5442**: `const response = await fetch(`/api/${realmId}/sprint/submit`, {`
  - **Linha 5501**: `const response = await fetch(`/api/${realmId}/sprint/leaderboard`, {`
  - **Linha 5566**: `const response = await fetch(`/api/${realmId}/friends/${encodeURIComponent(miner`
  - **Linha 5670**: `const response = await fetch(`/api/${realmId}/friends/add`, {`
  - **Linha 5704**: `const response = await fetch(`/api/${realmId}/friends/remove`, {`
  - **Linha 5779**: `const response = await fetch(`/api/${realmId}/crates/inventory/${encodeURICompon`
  - **Linha 5820**: `const response = await fetch(`/api/${realmId}/crates/open`, {`
  - **Linha 5941**: `const response = await fetch(`/api/${realmId}/level/${encodeURIComponent(minerNa`
  - **Linha 6002**: `const response = await fetch(`/api/${realmId}/level/${encodeURIComponent(minerNa`

- **Linha 4202**: `baseTimeLimit` — Usada em `applySkillBonuses` (linha 4202) mas nunca declarada. Deveria ser `networkTimeLimit`. **Impacto: crítico**. Sugestão: Corrigir referência ou declarar a variável.
- **Linha 4207**: `hintCost` — Usada em `applySkillBonuses` (linha 4207) mas nunca declarada. Deveria ser `HINT_PRICE`. **Impacto: crítico**. Sugestão: Corrigir referência ou declarar a variável.
- **Linha 5372**: `currentRoundWords` — Usada em `startSprintRound` (linha 5372) mas nunca declarada. **Impacto: crítico**. Sugestão: Corrigir referência ou declarar a variável.
- **Linha 5373**: `renderWordBank` — Chamada em `startSprintRound` (linha 5373) mas nunca declarada. **Impacto: crítico**. Sugestão: Corrigir referência ou declarar a variável.
- **Linha 5311**: `handleWebSocketMessage` — Monkey-patch na linha 5311 referencia função inexistente. O handler real é `socket.onmessage` inline. **Impacto: crítico**. Sugestão: Corrigir referência ou declarar a variável.

---

## Resumo

| Categoria | Quantidade | Impacto |
|---|---|---|
| Funções não chamadas | 8 | Baixo |
| Variáveis não usadas | 8 | Baixo |
| Event listeners duplicados | 4 | Médio |
| Memory leaks (timeouts inline) | 9 | Baixo-Médio |
| DOM inexistente | 13 | Crítico |
| Fetch sem error handling | 25 | Médio |
| Código duplicado (monkey-patches) | 23 | Médio |
| Código duplicado (blocos) | 4 pares | Baixo |
| Funções longas (>100 linhas) | 2 | Médio |
| Variáveis globais | 114 | Médio |
| Promises não awaitadas | 80 | Baixo |
| Callbacks aninhados (6+ níveis) | 17 | Baixo |
| Estado inconsistente | 30 | Crítico |