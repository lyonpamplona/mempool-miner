# Auditoria — Jogo Central (Tab JOGO)

> Auditoria 100% das mecânicas do jogo central do Mempool Miner.
> Escopo: geração de palavras, rodadas, grid, pontuação, raridades, modos especiais, energia, hardware, decoder.
> Arquivos auditados: `backend/app/engine.py`, `backend/app/config.py`, `backend/app/ingestor.py`, `backend/app/main.py`, `backend/app/storage.py`, `frontend/game.js`, `frontend/index.html`.
> Data: 2026-08-23.

---

## 1. Geração de palavras

### 1.1 Como o TXID vira palavra (BIP39, 128 bits)

| Etapa | Onde | Detalhe |
|---|---|---|
| TXID calculado | `backend/app/ingestor.py:446-450` | `hashlib.sha256(hashlib.sha256(bytes.fromhex(tx_hex)).digest()).digest()[::-1].hex()` — double SHA256 + reversão de bytes (formato Bitcoin). |
| Entropia | `backend/app/engine.py:92` | `entropy = bytes.fromhex(txid[:32])` — primeiros **128 bits** (32 hex chars) do TXID. |
| Palavra BIP39 | `backend/app/engine.py:93` | `Mnemonic("english").to_mnemonic(entropy).split()[0].upper()` — **primeira palavra** do mnemonic BIP39 **inglês**, em **MAIÚSCULAS**. |
| Fallback | `backend/app/engine.py:94-96` | TXID inválido (`len < 32` ou `ValueError`/`IndexError`) → `"BITCOIN"`. |
| Validação frontend | `frontend/game.js:1176-1190` | `isValidTransactionEvent` exige `word` casando `/^[A-Z]{1,15}$/`, `is_high_fee`/`is_golden` boolean, `vsize` number > 0. |

A palavra é derivada **no backend** (`GameEngine.tx_to_word`, `engine.py:83-96`) e viaja no evento `transaction_received` (`ingestor.py:486-501`) com os campos: `word`, `txid`, `tx_stub` (8 hex), `is_golden`, `is_high_fee`, `vsize`, `fee_rate_sat_vb`, `is_mev`, `base_reward` (500), `multiplier`.

### 1.2 O que acontece quando a tx é RBF / minerada

| Evento | Onde | Comportamento |
|---|---|---|
| Bloco minerado (backend) | `ingestor.py:543-615` (`handle_block`) | Epoch avança para o novo `block_hash`; `drain_stale_transactions` (`ingestor.py:293-321`) descarta TXs da epoch anterior da fila (preservando as da nova epoch); publica `block_mined` com `is_halving_block = blocks % 210000 == 0` (`ingestor.py:579`). |
| Bloco minerado (frontend) | `game.js:1663-1725` | Dedup por `block_hash`/`epoch` (`game.js:1668-1677`); limpa `txBuffer` (`game.js:1683`); se `isPlaying` → oferece **Orphan Block Salvage (RBF)** uma vez por rodada (`orphanOfferedThisRound`, `game.js:1705-1708`); senão `prepareNextBlock()` (`game.js:1724`). |
| RBF (resgate) | `game.js:3100-3153` | `RBF_PRICE = 100000` sats, `RBF_TIME_BONUS = 15` s. Se o jogador aceitar em 3s (`game.js:3119-3122`), debita 100K, reinicia a rodada com `networkTimeLimit = 15 + getNetworkTimeBonus()` (`game.js:3143`). Se recusar/expirar → `showResult(false, "O tempo de RBF expirou.")`. |

### 1.3 Dedup

| Camada | Onde | Mecanismo |
|---|---|---|
| Backend (TXID) | `storage.py:156-158` (`dedupe_key`), `ingestor.py:502-514` | Set Redis de TXIDs já publicados **por epoch** (`{realm}:seen:{epoch}`), TTL **3600s** (`COMMIT_TRANSACTION_SCRIPT`). |
| Frontend (palavra) | `game.js:1649` | `if (!txBuffer.find(t => t.word === data.word))` — ignora palavra duplicada no buffer da rodada. |
| Frontend (bloco) | `game.js:1668-1677` | Ignora `block_mined` com `block_hash`/`epoch` já processado (re-entrega ZMQ). |

---

## 2. Estrutura da rodada

### 2.1 Tamanho do grid

| Condição | Grid | Tempo | Onde |
|---|---|---|---|
| **Padrão** | **12×12** | 60s + bônus | `game.js:266` (`currentGridSize = 12`), `game.js:2339-2340` |
| Bloco pesado (`maxVsize > 1000`) | 15×15 | 75s + bônus | `game.js:2335-2337` |
| Lightning mode | 8×8 | 20s | `game.js:2332-2334` |
| Evento Lightning Storm | 8×8 | 20s | `game.js:2314-2317` |
| Evento Mempool Flood | 15×15 | 75s + bônus | `game.js:2318-2321` |
| Boss block | 15×15 | 45s + skill | `game.js:3641` |
| Sprint | 10×10 | 30s + skill | `main.py:4960`, `game.js:6684` |

### 2.2 Palavras por bloco

| Constante | Valor | Onde |
|---|---|---|
| `WORDS_PER_BLOCK` | **6** | `game.js:227` |
| Boss | **10** (`bossWordsRequired`) | `game.js:1242`, `ingestor.py:665` |
| Sprint | **4** (`SPRINT_WORD_COUNT`) | `main.py:4961` |

### 2.3 Posicionamento das palavras

| Aspecto | Detalhe | Onde |
|---|---|---|
| Direções | `[[1,0], [0,1], [1,1], [1,-1]]` — **horizontal →, vertical ↓, diagonal ↘, diagonal ↙** (sem reversas) | `game.js:2403` |
| Busca (validação) | Mesmas 4 direções, mas **bidirecional** (normaliza caminho forward/reverse) | `game.js:2464-2469` |
| Injeção | `injectWordInGrid` (`game.js:2400-2462`): até **200 tentativas aleatórias**; fallback determinístico (scan horizontal por linha vazia). Palavras > grid são truncadas (`game.js:2401`). |
| Preenchimento | `fillGridWithoutIncidentalWords` (`game.js:2509-2526`): letras A-Z aleatórias, até **50 tentativas**, rejeita se o filler criar uma palavra-alvo acidental. |
| Retry de build | `buildPlayableBlock` tenta até **4 vezes** (`game.js:2371-2373`); se falhar, "Falha ao montar a grade". |

### 2.4 Tempo limite da rodada (`networkTimeLimit`)

| Componente | Valor | Onde |
|---|---|---|
| Base | **60s** | `game.js:373` (`networkTimeLimit = 60`), `game.js:402` (`baseTimeLimit = 60`) |
| Bônus de hardware | `+10s × (hardwareLevel - 1)` | `game.js:2063`, `game.js:2137` |
| Bônus de nível | `min(level, 10)` s | `main.py:5086`, `game.js:7296` |
| Bônus de skill | `mining_time_bonus` (skill tree) | `game.js:5314-5325` |
| Halving penalty | `− min(roundNumber − 1, 30)` s (máx 30s) | `game.js:2343` |
| **Mínimo absoluto** | **15s** | `game.js:2345` (`Math.max(..., 15)`) |

Fórmula efetiva (padrão): `networkTimeLimit = max(60 + hardwareBonus + levelBonus + skillBonus − halvingPenalty, 15)`.

### 2.5 Fim de rodada: tempo esgotar vs todas as palavras

| Cenário | Comportamento | Onde |
|---|---|---|
| **Todas as palavras achadas** | `roundSettled = true` (`game.js:2909`); `showResult(true, ...)` após 600ms (`game.js:2919-2924`); `roundNumber++`, `trackBlockCompleted()`, `claimFreeCrates()` (`game.js:3086-3090`). |
| **Tempo esgotar** | Tick do timer verifica `roundSettled` (`game.js:3063`) — se `true`, **não** sobrescreve o sucesso. Se `false`, `showResult(false, "O cronômetro da rodada expirou.")` (`game.js:3065`). |
| Timer | `startNetworkRace` (`game.js:3021-3068`): `raceEndTime = now + networkTimeLimit*1000` (timestamp absoluto, imune a throttling de aba em 2º plano); tick a cada **250ms**. |

---

## 3. Pontuação

### 3.1 Base e halving

| Item | Valor | Onde |
|---|---|---|
| `baseReward` | **500** sats | `game.js:363`, `engine.py:208` |
| Halving (recompensa) | `−2%` a cada 10 blocos, **mín 50%** | `game.js:2347` (`halvingRewardFactor = max(1 − floor(round/10)*0.02, 0.5)`) |
| `effectiveBaseReward` | `floor(500 × halvingRewardFactor × globalRewardMultiplier)` | `game.js:2348` |

### 3.2 Multiplicadores

| Multiplicador | Valor | Onde |
|---|---|---|
| **Golden** (txid prefixo `00`) | **5×** | `engine.py:336-337` |
| **High Fee** (fee_rate ≥ 20 sat/vb) | **3×** | `engine.py:338-339` |
| **Golden + High Fee** | **15×** (5× × 3×) | `engine.py:330` (docstring), `engine.py:336-339` (código) |
| **MEV** | **1×** (sem multiplicador, bônus fixo à parte) | `engine.py:328` (docstring) |
| Combo | 1.0 → +0.5 a cada palavra em <8s, **teto 4.0** (6.0 com Double Combo) | `game.js:2807-2809` |
| Lightning mode | ×10 | `game.js:2820` |
| Magnet (powerup) | ×1.5 | `game.js:2822` |
| Boss | ×5 (`bossRewardMultiplier`) | `game.js:2828`, `game.js:1240` |
| Skill reward bonus | `×(1 + skillRewardBonus)` | `game.js:2814` |
| Achievement bonus | `floor(points × (1 + reward_percent))` | `game.js:3447-3450` |

### 3.3 Fórmula completa (score → sats)

```
points = (
    (effectiveBaseReward × (1 + skillRewardBonus))   # base ajustada por halving/evento/skill
    + (word.length × 50)                              # bônus por comprimento
) × comboMultiplier                                   # combo (1.0–4.0, 6.0 c/ Double Combo)
  × backendMultiplier                                 # golden 5× / high_fee 3× / golden+high_fee 15×
  [× 10 se lightningMode]
  [× 1.5 se magnet]
  = applyAchievementBonus(points)                    # floor(points × (1 + reward_percent))

balanceSatoshis += floor(points)                     # game.js:2868
currentRoundEarnings += floor(points)                # game.js:2867
```

**Bônus fixos (fora da fórmula):**
- MEV: **+50.000 sats** (`game.js:2858-2865`)
- Boss loot: **+50.000 sats** (`game.js:2846`, `game.js:1241`)

**Slashing (penalidade):** 3+ erros consecutivos → **5% do saldo** debitado (`game.js:370-371`, `game.js:2938-2951`). Power-up Precision isenta a rodada.

**XP por palavra:** `Math.round(word.length × 10 + comboMultiplier × 5)` (`game.js:7371-7378`).

**Score no leaderboard:** `submitScore()` envia `balanceSatoshis` como `score` (`game.js:1971`). `syncPlayerState()` envia `balance` + `hardware_level` + `combo_multiplier` para o backend (`game.js:2002-2012`).

> **Nota:** Não há "bônus de tempo restante" no fim da rodada. O "bônus de tempo" refere-se ao **tempo extra** concedido por hardware/nível/skill (seção 7), não a um acréscimo de sats por tempo sobrando.

---

## 4. Raridades

| Raridade | Critério | Prob. | Efeito visual/jogável | Onde |
|---|---|---|---|---|
| **is_golden** | `txid.startswith("00")` | ~1/256 (0.39%) | **5×** recompensa; label "(GOLDEN)" em dourado no floating text | `engine.py:159`, `game.js:2968` |
| **is_high_fee** | `fee_rate_sat_vb >= 20.0` | variável | **3×** recompensa; label "(HIGH FEE)" em laranja | `engine.py:187`, `config.py:130` (`HIGH_FEE_RATE_SAT_VB = 20.0`), `game.js:2972` |
| **is_mev** | `int(txid[:8], 16) % 100 < 15` | ~15% | **Palavra oculta** (não aparece no word bank); **+50.000 sats** ao encontrar; sem multiplicador | `engine.py:198`, `game.js:2428-2431` (injeção sem render), `game.js:2858-2865` (bônus) |
| **expand_grid** | `vsize > 1000` | variável | **15×15 grid + 75s** (em vez de 12×12 + 60s) | `engine.py:207`, `game.js:2335-2337` |

**Golden Rush (evento global):** força `is_golden = True` em ~30% das palavras (`int(word[:2], 16) % 100 < 30`) — **ver seção 9, item 1, bug ALTO** (`engine.py:388`).

---

## 5. Modos especiais

### 5.1 Boss block

| Parâmetro | Valor | Onde |
|---|---|---|
| Disparo | **A cada 50 blocos** (`count % 50 == 0`) | `ingestor.py:657-670` (script Lua `RESET_SCRIPT`) |
| HP | **10** (`boss_hp`) | `ingestor.py:663`, `game.js:1238` |
| Grid | **15×15** (`boss_grid_size`) | `ingestor.py:664`, `game.js:3641` (hardcoded) |
| Palavras | **10** (`boss_words`) | `ingestor.py:665`, `game.js:1242` |
| Timer | **45s** + `skillTimeBonus` (`boss_timer`) | `ingestor.py:666`, `game.js:3642` |
| Multiplicador | **5×** (`boss_reward_multiplier`) | `ingestor.py:667`, `game.js:1240` |
| Loot | **+50.000 sats** (`boss_loot`) | `ingestor.py:668`, `game.js:1241` |

**Regras:**
- Evento `boss_block` chega via WebSocket (`game.js:1735-1737` → `handleBossBlock`, `game.js:3500-3552`).
- Ignorado se `isPlaying`, `isTransitioning` ou modal de resultado ativo (`game.js:3502-3513`).
- Coleta **10 palavras** do buffer (`handleBossTransaction`, `game.js:3584-3617`), com dedup por palavra.
- Cada palavra encontrada causa **1 dano** ao boss (`game.js:2830`) e multiplica pontos por **5×** (`game.js:2828`).
- **HP ≤ 0** → boss derrotado: **+50.000 sats** de loot (`game.js:2846`), modal de derrota (`game.js:2851`), `roundNumber++` (`game.js:2915`).
- **Timer expira** → `showBossResult(false, "O cronômetro do boss expirou. O boss resistiu!")` (`game.js:3762`), `resetBossState()` (`game.js:3795`).
- Barra de HP muda de cor: verde → laranja (≤50%) → vermelha (≤20%) (`game.js:3573-3577`).

### 5.2 Sprint mode

| Parâmetro | Valor | Onde |
|---|---|---|
| Grid | **10×10** | `main.py:4960` (`SPRINT_GRID_SIZE`) |
| Palavras | **4** (aleatórias do wordlist BIP39 PT) | `main.py:4961`, `main.py:4995` |
| Tempo | **30s** + `skillTimeBonus` | `main.py:4962`, `game.js:6694` |
| Recompensa | **500 sats/palavra** (`words_found × 1000 × 0.5`) | `main.py:5015-5016` |
| Leaderboard | **Separado** (`sprint_leaderboard_key`), top 10, ordenado por **menor tempo** | `main.py:5022-5025`, `main.py:5034-5047` |

**Regras:**
- Ativação: botão "Sprint" (`game.js:6645-6655`) → `sprintMode = true`; a próxima `startNetworkRace()` dispara `startSprintRound()` (`game.js:6854-6861`).
- `startSprintRound` (`game.js:6661-6711`): POST `sprint/start` → backend gera 4 palavras; frontend monta grid 10×10, inicia countdown de 1s (`game.js:6736-6748`).
- `block_mined` encerra o sprint (`game.js:1698-1699`).
- `endSprintRound` (`game.js:6752-6780`): calcula `timeTaken`, chama `submitSprintResult` (`game.js:6783-6813`).
- Backend valida `time_taken ≤ 35s` (`SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS = 30 + 5`) (`main.py:4982-4985`).

### 5.3 Time freeze

| Aspecto | Detalhe | Onde |
|---|---|---|
| O que é | Power-up que **pausa o cronômetro por 5s** | `main.py:2144-2152` |
| Custo | **10.000 sats** (compra na loja) | `main.py:2149` (`price`) |
| Efeito | `powerupEffects.time_freeze += 5` (`game.js:508`, `game.js:538`) |
| Mecânica | No tick do timer, `raceEndTime += deltaMs` (adianta o endTime pelo tempo real do tick) e decrementa o freeze pelo tempo real (`game.js:3041-3048`) |
| Origem | Compra na loja de power-ups OU recompensa do Decoder (power-up aleatório) | `main.py:2144`, `main.py:4826` |

---

## 6. Energia

| Parâmetro | Valor | Onde |
|---|---|---|
| Custo por rodada | **1 energy** | `main.py:4499-4536` (`spend_energy`) |
| Máximo | **10** (`ENERGY_MAX`) | `main.py:4421` |
| Recarga automática | **1 energy a cada 30 min** (`ENERGY_REFILL_INTERVAL = 1800s`) | `main.py:4422`, `main.py:4477-4480` |
| Compra | **3 energy por 2.000 sats** (`ENERGY_BUY_COST = 2000`, `ENERGY_BUY_AMOUNT = 3`) | `main.py:4423-4424`, `main.py:4561-4601` |
| Sem energia | `showPendingEnergyState()` — "Energia insuficiente. Aguarde a recarga ou compre energia." (`game.js:2218-2230`) |
| Refund em falha | `queueEnergyRefund()` se a rodada não iniciar (`game.js:2259`, `game.js:2280`); `ENERGY_REFUND_SCRIPT` (`main.py:4538-4558`) |
| Idempotência | `ENERGY_ROUND_TTL = 86400` (24h para retry/refund) | `main.py:4425` |

---

## 7. Hardware

| Nível | Nome | Custo | Efeito | Onde |
|---|---|---|---|---|
| 1 | CPU Miner | — (inicial) | Base (0s extra) | `game.js:346` |
| 2 | GPU Rig | **100.000 sats** | **+10s** no tempo da rodada | `game.js:347`, `game.js:2063` |
| 3 | ASIC Antminer | **500.000 sats** | **+20s** no tempo da rodada | `game.js:347`, `game.js:2063` |
| 4 | Quantum Node | **2.000.000 sats** | **+30s** no tempo da rodada | `game.js:347`, `game.js:2063` |

**Mecânica:** `networkTimeBonus = (hardwareLevel − 1) × 10` (`game.js:2063`, `game.js:2137`). O bônus é somado ao `networkTimeLimit` via `getNetworkTimeBonus()` (`game.js:351-353`), que também inclui o `levelTimeBonus` (`min(level, 10)` s, `main.py:5086`).

**Compra:** `buyHardware()` (`game.js:2128-2145`) — debita do saldo, incrementa `hardwareLevel`, atualiza UI, `submitScore()`, `saveSessionState()`.

---

## 8. Decoder

| Aspecto | Detalhe | Onde |
|---|---|---|
| O que é | Mini-game: adivinhar uma palavra BIP39 a partir de um **TXID truncado** + **primeira letra** | `main.py:4717-4778` |
| Frequência | **A cada 3 rodadas** (`DECODER_ROUNDS_INTERVAL = 3`) | `game.js:4929`, `game.js:4945-4951` |
| Tempo | **30s** (`DECODER_TIME_LIMIT = 30`) | `game.js:4928` |
| Cooldown backend | **180s** entre partidas (`DECODER_COOLDOWN_SECONDS`) | `main.py:4699` |
| Wordlist | Subconjunto BIP39 **português** (diferente do inglês do jogo principal) | `main.py:4609+` |
| TXID truncado | `0x{sha256(word)[:4]}...{sha256(word)[-4:]}` | `main.py:4753-4754` |
| Dica | Primeira letra da palavra (maiúscula) | `main.py:4757` |
| Recompensa (acerto) | **+5.000 sats** + **1 power-up aleatório** | `main.py:4823`, `main.py:4826-4827` |
| Streak/Wins | Persistidos em Redis (TTL 24h) | `main.py:4818-4819` |
| Timeout | "Tempo esgotado! Tente novamente mais tarde." | `game.js:5104-5114` |

**Fluxo:** `checkDecoderAvailability()` (`game.js:4945-4951`) mostra o botão a cada 3 rodadas → `startDecoderGame()` (`game.js:4956-5019`) → POST `decoder/start` → modal com TXID + dica + timer 30s → `submitDecoderAnswer()` (`game.js:5035+`) → POST `decoder/submit` → feedback + recompensa.

---

## 9. Pontas soltas

| # | Severidade | Descrição | Onde |
|---|---|---|---|
| 1 | **ALTO** | **Golden Rush: `int(word[:2], 16)` quebra para palavras iniciadas com G-Z.** O backend usa `int(tx_metadata.get("word", "A")[:2], 16) % 100 < 30` para forçar `is_golden` durante Golden Rush (`engine.py:388`). Mas `word` é uma **palavra BIP39 em letras** (ex: "GALAXY"), não hex. `int("GA", 16)` lança `ValueError` → a transação é **descartada silenciosamente** (`process_transactions` catch `ValueError`, `ingestor.py:535-536`). Durante Golden Rush, **todas as TXs cuja palavra começa com G-Z somem**. | `engine.py:388` |
| 2 | **ALTO** | **Double-counting de multiplicadores em eventos globais.** O backend aplica o multiplicador do evento **no `multiplier` da TX** (`apply_event_effects`, `engine.py:374-401`), e o frontend **também** aplica `globalRewardMultiplier` no `effectiveBaseReward` (`game.js:2313-2348`). Resultado: Fee Spike → 3× (backend) × 3× (frontend) = **9×** (deveria ser 3×); Golden Rush → 5× × 5× = **25×** para palavras golden; Mempool Flood → 2× × 2× = **4×**; Lightning Storm → 10× × 10× = **100×**. Além disso, no Golden Rush o frontend aplica 5× a **todas** as palavras da rodada (`game.js:2327-2328`), enquanto o backend só marca ~30% como golden — ou seja, palavras comuns também recebem 5× no frontend, divergindo da docstring do backend ("Golden Hash 3× mais frequente (5× recompensa)", `engine.py:386`). | `engine.py:374-401` + `game.js:2313-2348` |
| 3 | **MÉDIO** | **Boss block não consome energia.** `buildBossPlayableBlock()` (`game.js:3623`) não chama `requestPlayableBlockBuild()`/`spendEnergy()` — a rodada do boss é **gratuita** (sem gasto de energia). Pode ser intencional, mas diverge do fluxo normal. | `game.js:3623-3717` |
| 4 | **MÉDIO** | **`boss_grid_size` enviado pelo backend é ignorado.** O backend publica `boss_grid_size = 15` (`ingestor.py:664`), mas o frontend hardcodeia `currentGridSize = 15` (`game.js:3641`) e não lê o campo. Se o backend mudar o valor, o frontend não acompanha. | `ingestor.py:664` vs `game.js:3641` |
| 5 | **MÉDIO** | **`expand_grid` enviado pelo backend não é usado pelo frontend.** O backend calcula `expand_grid = vsize > 1000` (`engine.py:207`) e envia no evento, mas o frontend recalcula `maxVsize > 1000` a partir do `vsize` (`game.js:2335`). Redundante, mas consistente. | `engine.py:207` vs `game.js:2335` |
| 6 | **MÉDIO** | **Sprint: `skillTimeBonus` pode exceder o teto do backend.** O frontend usa `sprintTimeLimit = time_limit + skillTimeBonus` (`game.js:6694`), mas o backend valida `time_taken ≤ 35s` (`SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS = 30 + 5`, `main.py:4982-4985`). Se `skillTimeBonus > 5`, o frontend pode exceder 35s e o backend **rejeita o submit** (HTTP 422). | `game.js:6694` vs `main.py:4982-4985` |
| 7 | **MÉDIO** | **Decoder usa wordlist PT; jogo principal usa BIP39 EN.** O decoder sorteia palavras de um subconjunto **português** (`main.py:4609+`), mas o jogo principal deriva palavras do BIP39 **inglês** (`engine.py:44`). Inconsistência de vocabulário entre as duas mecânicas. | `main.py:4609+` vs `engine.py:44` |
| 8 | **BAIXO** | **RBF: rodada de resgate tem apenas 15s + bônus.** `networkTimeLimit = RBF_TIME_BONUS + getNetworkTimeBonus()` (`game.js:3143`) — a rodada RBF tem **15s** (não o tempo original da rodada). Muito curto para 6 palavras. | `game.js:3143` |
| 9 | **BAIXO** | **Boss: `showBossDefeatModal` agendado em 1000ms pode sobrepor-se ao resultado.** Se o jogador encontrar as palavras restantes dentro de 1s após a derrota do boss, o modal de derrota do boss (`game.js:2851`) pode sobrepor-se ao modal de resultado normal. | `game.js:2851` |
| 10 | **BAIXO** | **Boss: `handleBossBlock` ignorado se `isPlaying`.** Se o evento `boss_block` chegar durante uma rodada em andamento, é **silenciosamente descartado** (`game.js:3506-3508`). O boss só dispara entre rodadas. | `game.js:3506-3508` |
| 11 | **BAIXO** | **`injectWordInGrid` trunca palavras > grid.** `word = word.substring(0, currentGridSize)` (`game.js:2401`). Palavras BIP39 têm máx 8 letras, então nunca dispara em grids ≥8×8, mas é um comportamento silencioso. | `game.js:2401` |
| 12 | **BAIXO** | **`fillGridWithoutIncidentalWords` pode falhar.** Após 50 tentativas, se o filler ainda criar palavras acidentais, `buildPlayableBlock` retry (até 4×). Se todos falharem, "Falha ao montar a grade" e a rodada não inicia (`game.js:2371-2378`). | `game.js:2509-2526`, `game.js:2371-2378` |
