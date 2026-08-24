# Auditoria de Mecânicas — 03: Progressão

> Auditoria 100% da progressão do Mempool Miner (XP, níveis, season pass, skill tree, cards, missões, leaderboard).
> Valores exatos extraídos do código, com `path:linha`. Estado: pós-Fases 1–8 + auditoria final.

## 1. XP

- **Por palavra (única fonte de XP)**: `frontend/game.js:7371-7378` — `calculateWordXP()`: `baseXP = word.length * 10; comboBonus = comboMultiplier * 5; return Math.round(baseXP + comboBonus)`. Aplicado em `game.js:2877-2879`: 100% do XP da palavra vai **tanto** para o nível do jogador (`addXP`) **quanto** para o season pass (`addSeasonXP`).
- **Rodada/bônus**: NÃO há XP por rodada completa nem por bônus (MEV, boss, golden) — busca por `roundXP|bonusXP|XP_BONUS` retornou 0 resultados.
- **Combo**: `game.js:2807-2809` — começa 1.0, +0.5 a cada palavra em <8s, teto 4.0 (6.0 com powerup `double_combo`).
- **Curva de nível**: `backend/app/main.py:5078-5080` — `xp_to_next_level(level) = level * 100` (linear, sem teto). Loop de level-up: `main.py:5165-5168`. XP total p/ nível N = `100·N·(N−1)/2` (fórmula em `main.py:5181`).
- **Curva de season**: fixa `SEASON_XP_PER_LEVEL = 100` (`season_pass.py:13`), teto nível 40 (`season_pass.py:201-206`).
- **Bug float (corrigido)**: `season_pass.py:188` — `xp_amount = int(float(xp_amount))` e leituras `int(float(raw.get("xp", 0)))` em `season_pass.py:123,197` (comentário 120-122: `int("67.5")` lançava ValueError → 500). Frontend: `Math.round` em `game.js:7377` (comentário 7374-7376).
- **Estado atual**: season seguro; **endpoint de nível AINDA vulnerável** — `main.py:5151,5161,5171` grava `str(xp)` sem coerção `int(float)`; se chegar float, grava `"67.5"` e a próxima leitura `int()` (`main.py:5119,5158`) quebra com 500. Mitigado só pelo `Math.round` do frontend.

## 2. Níveis

- Sem teto de nível. Ranks: `main.py:5055-5067` — 1-9 Script Kiddie, 10-19 Node Operator, 20-29 Hash Crafter, 30-39 Block Miner, 40-49 Mempool Hunter, 50-59 Satoshi Disciple, 60-69 Chain Validator, 70-79 Hash Rate Lord, 80-89 Block King, 90-99 Bitcoin Legend, 100 Satoshi.
- Bônus passivos: `main.py:5083-5091` — `time_bonus_seconds = min(level, 10)` (máx +10s), `hint_discount_percent = min((level//3)*10, 30)` (máx 30%).
- Aplicação no jogo: `game.js:7296` (`levelTimeBonus`), `game.js:349-352` (tempo efetivo = network + level), `game.js:7324` (`window.HINT_DISCOUNT`).
- Pontos de skill: 1 a cada 10 níveis (`main.py:1658-1663`).
- Bug menor: `game.js:7346` — ao level-up, `xp_progress` vira 0 em vez do resto real.

## 3. Season Pass

- Constantes: `season_pass.py:10-14` — `SEASON_DURATION_DAYS=28` (**não usada**), FREE=20, PREMIUM=20 (níveis 21-40), `XP_PER_LEVEL=100`, `PREMIUM_UNLOCK_DAYS=7` (**não usada**).
- Duração real: **trimestre** (`season_pass.py:72-101`): Q1→04/01, Q2→07/01, Q3→10/01, Q4→01/01. Season ID: `season_{ano}_q{trimestre}` (`season_pass.py:64-69`).
- Recompensas free (níveis 1-20): `season_pass.py:17-38` — sats 500→25.000, hints 1/2/3 (nív. 3, 9, 15), powerups scanner (6), time_freeze (12), magnet (18), nível 20: 25.000 sats + `season_badge`.
- Recompensas premium (21-40): `season_pass.py:40-61` — sats 30.000→250.000, cards rare (22, 38), epic (26, 34), legendary (30), powerups precision (24), double_combo (28), scanner (36), bonus `reward_plus_5pct` 7d (32) e `reward_plus_10pct` 14d (40).
- Premium: 50.000 sats (`season_pass.py:324`), compra atômica Lua (`season_pass.py:326-344`).
- Claim: Lua `season_pass.py:246-286` — **só credita `sats`, `hint`, `powerup`**. Tipos `card`, `bonus`, `season_badge` são marcados como reclamados **sem creditar nada**.
- Fim da temporada: **nenhuma lógica de rollover/claim-deadline**; chave com TTL 30 dias (`season_pass.py:212,284,342`).
- Frontend: `game.js:5679-5900` (load, render, claim, buy, timer 30s).

## 4. Skill Tree (tab PERFIL)

- 3 ramos × 5 níveis: `main.py:1609-1646` — **Mining** +1s→+5s tempo base; **Search** hints −10%→−50%; **Lightning** +5%→+25% recompensa.
- Custo: 1 ponto/nó; pontos = `player_level // 10` (`main.py:1658-1663`); **sem pré-requisitos entre ramos**; máx 5/ramo.
- Bônus: `main.py:1666-1676`. Upgrade: `main.py:1759-1839` (Lua 1789-1813, TTL 86400).
- Aplicação: `game.js:5313-5328` — `baseTimeLimit = 60 + skillTimeBonus`; `hintCost = HINT_PRICE*(1−desconto)`; `skillRewardBonus` usado em `game.js:2814`.
- **Ponta solta crítica**: chave de skills com TTL 24h (`main.py:1714,1820`) — se o jogador não abrir o PERFIL por 1 dia, a árvore **reseta** (níveis perdidos, pontos recalculados).

## 5. Cards

- Raridades: `main.py:3472-3505` — common 60%, rare 25%, epic 10%, legendary 5%.
- Geração: `ingestor.py:747-767` — **rolagem pura aleatória** (docstring 696-700 alega base em eventos: MEV/Boss/High Fee/Golden/evento global — **divergência doc/código**). Um card por bloco (`ingestor.py:688-745`), salvo global.
- Como se ganha: (a) **bloco** — todo jogador conectado recebe via WS `block_mined` → `creditBlockCard` (`game.js:1694-1696, 6078-6093`) → `POST cards/{username}/credit` (`main.py:3604-3653`); (b) **crate** — 12% rare/epic (`main.py:3727-3737`, crédito efetivo não verificado); (c) **season premium** — níveis 22/26/30/34/38 (não implementado no claim); (d) **mercado** — não existe para cards (mercado é só power-ups).
- Bônus de coleção: `main.py:3508-3513` — common 10→+1%, rare 5→+2%, epic 3→+3%, legendary 1→+5%; calculado em `main.py:3558-3567` mas **aplicação nas recompensas não verificada**.
- Sem efeito individual por card.

## 6. Missões

- 6 diárias (`main.py:1259-1314`): `find_5_high_fee` (5 High Fee, 2.000), `earn_50k_round` (50K sats/rodada, 3.000), `use_rbf` (1 RBF, 5.000), `find_3_mev` (3 MEV, 10.000), `complete_3_blocks` (3 blocos, 4.000), `10_words_no_error` (10 palavras, 2.500). Rotação: 3 de 6 por `day_of_year % 3` (`main.py:1317-1323`).
- Semanal: `find_100_words_week` (100 palavras, 50.000 sats + achievement `weekly_miner_champion`) — `main.py:1368-1377`.
- Progresso: `POST /update` (`main.py:1506-1602`). Claim: `POST /claim/{mission_id}` (`main.py:1426-1503`) — **correção persist**: `main.py:1491` `persist(state_key)` (comentário 1488-1490: remove o 8º `expire(86400)` que expirava o saldo em 24h). TTL da chave de missões: 8 dias (`main.py:1483`).
- Painel: **tab COMPETIR** (`game.js:575-579`, `section-competir-missions`; correção da auditoria Fase 5). Claim frontend: `game.js:4033-4081`.
- Ponta solta: `10_words_no_error` usa stat cumulativo `words_found` (`main.py:1546`) — "consecutivas sem erro" não é rastreado.

## 7. Leaderboard

- Global: `ZADD GT CH` (`main.py:766-771`), top 10 (`main.py:800-803`), chave `storage.py:141-143`. Pools: `ZADD GT CH` por `pool_name` (`main.py:776-781`), top 10 (`main.py:819-822`), chave `storage.py:183-185`.
- Score = `balanceSatoshis` (saldo total), enviado após cada palavra (`game.js:2899, 1958-1986`).
- **Reset por epoch: a cada 2016 blocos** — `ingestor.py:640-655` (del leaderboard + pools, incrementa `epoch_id`, publica `leaderboard_reset`). Frontend: `game.js:1728-1731` ("Nova temporada! Leaderboard resetado").
- Sprint tem leaderboard separado (`storage.py:334-336`).

## 8. Pontas soltas (severidade)

| Severidade | Item | Local |
|---|---|---|
| **ALTO** | Endpoint de nível sem `int(float)` — bug float só corrigido no season | `main.py:5137-5186` |
| **ALTO** | Recompensas season `card`/`bonus`/`season_badge` marcadas como reclamadas sem creditar | `season_pass.py:274-280` |
| **ALTO** | Skill tree com TTL 24h — reseta após 1 dia sem abrir PERFIL | `main.py:1714,1820` |
| MÉDIA | Raridade de card: docstring alega eventos, código é aleatório puro | `ingestor.py:696-700 vs 747-767` |
| MÉDIA | Bônus de coleção calculado mas aplicação nas recompensas não verificada | `main.py:3508-3513` |
| MÉDIA | Sem lógica de fim de temporada (rollover, carryover, prazo de claim) | `season_pass.py` |
| MÉDIA | Missão "sem erro" não rastreia erro (usa `words_found` cumulativo) | `main.py:1546` |
| BAIXA | `SEASON_DURATION_DAYS=28` e `PREMIUM_UNLOCK_DAYS=7` definidos e não usados | `season_pass.py:10,14` |
| BAIXA | `xp_progress=0` ao level-up (UI) | `game.js:7346` |
| BAIXA | Drop de card em crate: crédito efetivo não verificado | `main.py:3727-3737` |
| OBS | XP só por palavra (sem XP de rodada/bônus) — documentar como design | `game.js:2877-2879` |
